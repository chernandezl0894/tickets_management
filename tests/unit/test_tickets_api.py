"""Tests for the ticket API endpoints."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from tickets_management.domain.enum import Platform
from tickets_management.domain.models import Project, Subtask
from tickets_management.repositories.errors import NotFoundError
from tickets_management.repositories.memory import InMemoryStore


def _make_project(slug: str = "tickets", *, is_active: bool = True) -> Project:
    """Build a project entity for seeding."""
    return Project(
        name=f"Project {slug}",
        slug=slug,
        platform=Platform.GITHUB,
        repo_url=f"https://github.com/example/{slug}",
        is_active=is_active,
    )


def _ticket_payload(project_id: UUID, **overrides: object) -> dict[str, object]:
    """Build a valid ticket payload."""
    payload: dict[str, object] = {
        "project_id": str(project_id),
        "type": "feature",
        "title": "Valid ticket title",
        "description": "Ticket description",
        "priority": "medium",
    }
    payload.update(overrides)
    return payload


def _due_in(days: int) -> str:
    """Return an ISO due date in the future."""
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def test_create_ticket_returns_201(client: TestClient, store: InMemoryStore) -> None:
    """POST /tickets creates a ticket in an active project."""
    project = store.projects.add(_make_project())

    response = client.post("/api/v1/tickets", json=_ticket_payload(project.id))

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == str(project.id)
    assert body["priority"] == "medium"
    assert body["status"] == "open"


def test_create_ticket_in_missing_project_returns_404(
    client: TestClient,
) -> None:
    """POST /tickets returns 404 when the project does not exist."""
    response = client.post(
        "/api/v1/tickets",
        json=_ticket_payload(UUID(int=0)),
    )

    assert response.status_code == 404


def test_create_ticket_in_inactive_project_returns_409(
    client: TestClient, store: InMemoryStore
) -> None:
    """POST /tickets returns 409 when the project is inactive."""
    project = store.projects.add(_make_project("inactive", is_active=False))

    response = client.post("/api/v1/tickets", json=_ticket_payload(project.id))

    assert response.status_code == 409
    assert "not active" in response.json()["detail"]


def test_list_tickets_filters_by_priority_and_status(
    client: TestClient, store: InMemoryStore
) -> None:
    """Combined priority and status filters return only matching tickets."""
    project = store.projects.add(_make_project())
    client.post(
        "/api/v1/tickets",
        json=_ticket_payload(project.id, priority="high", status="open"),
    )
    client.post(
        "/api/v1/tickets",
        json=_ticket_payload(project.id, priority="high", status="done"),
    )
    client.post(
        "/api/v1/tickets",
        json=_ticket_payload(project.id, priority="low", status="open"),
    )

    response = client.get(
        "/api/v1/tickets", params={"priority": "high", "status": "open"}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["priority"] == "high"
    assert body[0]["status"] == "open"


def test_list_tickets_filters_by_project_and_type(
    client: TestClient, store: InMemoryStore
) -> None:
    """Project and type filters can be combined."""
    first = store.projects.add(_make_project("first"))
    second = store.projects.add(_make_project("second"))
    client.post("/api/v1/tickets", json=_ticket_payload(first.id, type="feature"))
    client.post("/api/v1/tickets", json=_ticket_payload(first.id, type="issue"))
    client.post("/api/v1/tickets", json=_ticket_payload(second.id, type="feature"))

    response = client.get(
        "/api/v1/tickets",
        params={"project_id": str(first.id), "type": "issue"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_tickets_orders_by_priority_then_due_at(
    client: TestClient, store: InMemoryStore
) -> None:
    """Tickets are ordered by priority descending and due date ascending."""
    project = store.projects.add(_make_project())
    client.post(
        "/api/v1/tickets",
        json=_ticket_payload(
            project.id, title="low-soon", priority="low", due_at=_due_in(1)
        ),
    )
    client.post(
        "/api/v1/tickets",
        json=_ticket_payload(
            project.id, title="high-late", priority="high", due_at=_due_in(5)
        ),
    )
    client.post(
        "/api/v1/tickets",
        json=_ticket_payload(
            project.id, title="medium-late", priority="medium", due_at=_due_in(2)
        ),
    )
    client.post(
        "/api/v1/tickets",
        json=_ticket_payload(
            project.id, title="high-soon", priority="high", due_at=_due_in(1)
        ),
    )

    response = client.get("/api/v1/tickets")

    assert [ticket["title"] for ticket in response.json()] == [
        "high-soon",
        "high-late",
        "medium-late",
        "low-soon",
    ]


def test_type_filter_rejects_values_outside_the_enum(client: TestClient) -> None:
    """The type filter only accepts TicketType values."""
    response = client.get("/api/v1/tickets", params={"type": "epic"})

    assert response.status_code == 422


def test_get_and_delete_ticket(client: TestClient, store: InMemoryStore) -> None:
    """A ticket can be fetched and deleted."""
    project = store.projects.add(_make_project())
    created = client.post("/api/v1/tickets", json=_ticket_payload(project.id)).json()

    assert client.get(f"/api/v1/tickets/{created['id']}").status_code == 200
    assert client.delete(f"/api/v1/tickets/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/tickets/{created['id']}").status_code == 404


def test_mark_done_with_pending_subtasks_returns_409(
    client: TestClient, store: InMemoryStore
) -> None:
    """A ticket with pending subtasks cannot be marked as done."""
    project = store.projects.add(_make_project())
    created = client.post("/api/v1/tickets", json=_ticket_payload(project.id)).json()
    ticket_id = UUID(created["id"])
    for title in ("First pending", "Second pending"):
        store.subtasks.add(Subtask(ticket_id=ticket_id, title=title))

    response = client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "done"})

    assert response.status_code == 409
    assert "2" in response.json()["detail"]


def test_mark_done_without_pending_subtasks_succeeds(
    client: TestClient, store: InMemoryStore
) -> None:
    """A ticket can be marked as done once its subtasks are completed."""
    project = store.projects.add(_make_project())
    created = client.post("/api/v1/tickets", json=_ticket_payload(project.id)).json()
    ticket_id = UUID(created["id"])
    subtask = store.subtasks.add(Subtask(ticket_id=ticket_id, title="Pending subtask"))
    subtask.is_done = True
    store.subtasks.update(subtask)

    response = client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "done"})

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_delete_ticket_cascades_to_subtasks(
    client: TestClient, store: InMemoryStore
) -> None:
    """Deleting a ticket removes its subtasks."""
    project = store.projects.add(_make_project())
    created = client.post("/api/v1/tickets", json=_ticket_payload(project.id)).json()
    ticket_id = UUID(created["id"])
    subtask = store.subtasks.add(Subtask(ticket_id=ticket_id, title="Pending subtask"))

    response = client.delete(f"/api/v1/tickets/{ticket_id}")

    assert response.status_code == 204
    with pytest.raises(NotFoundError):
        store.tickets.get(ticket_id)
    with pytest.raises(NotFoundError):
        store.subtasks.get(subtask.id)
