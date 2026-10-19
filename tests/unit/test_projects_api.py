"""Tests for the project API endpoints."""

from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from tickets_management.api.deps import get_store
from tickets_management.domain.enum import TicketType
from tickets_management.domain.models import Subtask, Ticket
from tickets_management.main import app
from tickets_management.repositories.errors import NotFoundError
from tickets_management.repositories.memory import InMemoryStore


@pytest.fixture
def store() -> InMemoryStore:
    """Return a fresh in-memory store for each test."""
    return InMemoryStore()


@pytest.fixture
def client(store: InMemoryStore) -> Iterator[TestClient]:
    """Return a client bound to the fresh store."""
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _payload(slug: str = "tickets") -> dict[str, str]:
    """Build a valid project payload."""
    return {
        "name": "Tickets Management",
        "slug": slug,
        "platform": "github",
        "repo_url": f"https://github.com/example/{slug}",
        "description": "Centralized ticket management service.",
    }


def test_create_project_returns_201(client: TestClient) -> None:
    """POST /projects creates a project and returns 201."""
    response = client.post("/api/v1/projects", json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["slug"] == "tickets"
    assert UUID(body["id"])


def test_create_project_with_duplicate_slug_returns_409(
    client: TestClient,
) -> None:
    """Creating two projects with the same slug returns 409."""
    assert client.post("/api/v1/projects", json=_payload()).status_code == 201

    response = client.post("/api/v1/projects", json=_payload())

    assert response.status_code == 409
    assert "tickets" in response.json()["detail"]


def test_list_projects_returns_total_and_respects_pagination(
    client: TestClient,
) -> None:
    """GET /projects returns the total and honors limit and offset."""
    for slug in ("alpha", "beta", "gamma"):
        assert client.post("/api/v1/projects", json=_payload(slug)).status_code == 201

    first_page = client.get("/api/v1/projects", params={"limit": 2, "offset": 0})
    assert first_page.status_code == 200
    assert first_page.json()["total"] == 3
    assert len(first_page.json()["items"]) == 2
    assert first_page.headers["x-total-count"] == "3"

    second_page = client.get("/api/v1/projects", params={"limit": 2, "offset": 2})
    assert second_page.json()["total"] == 3
    assert len(second_page.json()["items"]) == 1


def test_get_project_returns_404_when_missing(client: TestClient) -> None:
    """GET /projects/{id} returns 404 for an unknown id."""
    response = client.get(f"/api/v1/projects/{uuid4()}")

    assert response.status_code == 404


def test_patch_updates_name(client: TestClient) -> None:
    """PATCH /projects/{id} applies a partial update."""
    created = client.post("/api/v1/projects", json=_payload()).json()

    response = client.patch(
        f"/api/v1/projects/{created['id']}", json={"name": "Renamed"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_patch_without_fields_keeps_updated_at(client: TestClient) -> None:
    """PATCH with an empty body does not modify updated_at."""
    created = client.post("/api/v1/projects", json=_payload()).json()

    response = client.patch(f"/api/v1/projects/{created['id']}", json={})

    assert response.status_code == 200
    assert response.json()["updated_at"] == created["updated_at"]


def test_patch_rejects_slug_used_by_another_project(
    client: TestClient,
) -> None:
    """PATCH returns 409 when the new slug belongs to another project."""
    first = client.post("/api/v1/projects", json=_payload("alpha")).json()
    second = client.post("/api/v1/projects", json=_payload("beta")).json()

    response = client.patch(
        f"/api/v1/projects/{second['id']}", json={"slug": first["slug"]}
    )

    assert response.status_code == 409
    assert "alpha" in response.json()["detail"]


def test_patch_missing_project_returns_404(client: TestClient) -> None:
    """PATCH returns 404 for an unknown id."""
    response = client.patch(f"/api/v1/projects/{uuid4()}", json={"name": "Nope"})

    assert response.status_code == 404


def test_delete_project_returns_204(client: TestClient, store: InMemoryStore) -> None:
    """DELETE /projects/{id} removes the project and returns 204."""
    created = client.post("/api/v1/projects", json=_payload()).json()

    response = client.delete(f"/api/v1/projects/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    with pytest.raises(NotFoundError):
        store.projects.get(UUID(created["id"]))


def test_delete_project_cascades_to_tickets_and_subtasks(
    client: TestClient, store: InMemoryStore
) -> None:
    """Deleting a project also deletes its tickets and their subtasks."""
    created = client.post("/api/v1/projects", json=_payload()).json()
    other_created = client.post("/api/v1/projects", json=_payload("other")).json()
    project_id = UUID(created["id"])
    other_project_id = UUID(other_created["id"])

    ticket = store.tickets.add(
        Ticket(
            project_id=project_id,
            type=TicketType.FEATURE,
            title="Valid ticket title",
        )
    )
    subtask = store.subtasks.add(
        Subtask(ticket_id=ticket.id, title="Valid subtask title")
    )
    other_ticket = store.tickets.add(
        Ticket(
            project_id=other_project_id,
            type=TicketType.FEATURE,
            title="Another valid ticket",
        )
    )

    response = client.delete(f"/api/v1/projects/{project_id}")

    assert response.status_code == 204
    with pytest.raises(NotFoundError):
        store.projects.get(project_id)
    with pytest.raises(NotFoundError):
        store.tickets.get(ticket.id)
    with pytest.raises(NotFoundError):
        store.subtasks.get(subtask.id)
    assert store.tickets.get(other_ticket.id) == other_ticket


def test_delete_missing_project_returns_404(client: TestClient) -> None:
    """DELETE returns 404 for an unknown id."""
    response = client.delete(f"/api/v1/projects/{uuid4()}")

    assert response.status_code == 404
