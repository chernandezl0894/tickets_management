"""Tests for the nested subtask endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient

from tickets_management.domain.enum import Platform
from tickets_management.domain.models import Project
from tickets_management.repositories.memory import InMemoryStore


def _create_ticket(
    client: TestClient, store: InMemoryStore, slug: str = "tickets"
) -> dict[str, object]:
    """Create a project and a ticket, returning the ticket payload."""
    project = store.projects.add(
        Project(
            name=f"Project {slug}",
            slug=slug,
            platform=Platform.GITHUB,
            repo_url=f"https://github.com/example/{slug}",
        )
    )
    response = client.post(
        "/api/v1/tickets",
        json={
            "project_id": str(project.id),
            "type": "feature",
            "title": "Valid ticket title",
        },
    )
    body: dict[str, object] = response.json()
    return body


def _create_subtask(
    client: TestClient, ticket_id: str, title: str
) -> dict[str, object]:
    """Create a subtask and return its payload."""
    response = client.post(
        f"/api/v1/tickets/{ticket_id}/subtasks", json={"title": title}
    )
    body: dict[str, object] = response.json()
    return body


def test_create_subtask_appends_to_the_end(
    client: TestClient, store: InMemoryStore
) -> None:
    """New subtasks always receive the next position."""
    ticket = _create_ticket(client, store)
    ticket_id = str(ticket["id"])

    first = _create_subtask(client, ticket_id, "First subtask")
    second = _create_subtask(client, ticket_id, "Second subtask")

    assert first["position"] == 0
    assert second["position"] == 1


def test_list_subtasks_is_ordered_by_position(
    client: TestClient, store: InMemoryStore
) -> None:
    """GET returns the checklist ordered by position."""
    ticket = _create_ticket(client, store)
    ticket_id = str(ticket["id"])
    for title in ("First subtask", "Second subtask", "Third subtask"):
        assert (
            client.post(
                f"/api/v1/tickets/{ticket_id}/subtasks", json={"title": title}
            ).status_code
            == 201
        )

    response = client.get(f"/api/v1/tickets/{ticket_id}/subtasks")

    assert response.status_code == 200
    assert [subtask["title"] for subtask in response.json()] == [
        "First subtask",
        "Second subtask",
        "Third subtask",
    ]


def test_update_subtask_can_rename_and_mark_done(
    client: TestClient, store: InMemoryStore
) -> None:
    """PATCH can rename a subtask and toggle its completion state."""
    ticket = _create_ticket(client, store)
    ticket_id = str(ticket["id"])
    subtask = _create_subtask(client, ticket_id, "Original title")

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}/subtasks/{subtask['id']}",
        json={"title": "Renamed subtask", "is_done": True},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed subtask"
    assert response.json()["is_done"] is True


def test_delete_middle_subtask_reorders_remaining_positions(
    client: TestClient, store: InMemoryStore
) -> None:
    """Deleting a middle subtask leaves positions without gaps."""
    ticket = _create_ticket(client, store)
    ticket_id = str(ticket["id"])
    first = _create_subtask(client, ticket_id, "First subtask")
    second = _create_subtask(client, ticket_id, "Second subtask")
    third = _create_subtask(client, ticket_id, "Third subtask")

    response = client.delete(f"/api/v1/tickets/{ticket_id}/subtasks/{second['id']}")

    assert response.status_code == 204
    listed = client.get(f"/api/v1/tickets/{ticket_id}/subtasks").json()
    assert [subtask["id"] for subtask in listed] == [first["id"], third["id"]]
    assert [subtask["position"] for subtask in listed] == [0, 1]


def test_subtask_from_another_ticket_returns_404(
    client: TestClient, store: InMemoryStore
) -> None:
    """A subtask can only be accessed through its owning ticket."""
    first_ticket = _create_ticket(client, store, "first")
    second_ticket = _create_ticket(client, store, "second")
    subtask = _create_subtask(client, str(first_ticket["id"]), "Owned subtask")
    wrong_url = f"/api/v1/tickets/{second_ticket['id']}/subtasks/{subtask['id']}"

    assert client.patch(wrong_url, json={"is_done": True}).status_code == 404
    assert client.delete(wrong_url).status_code == 404


def test_create_subtask_in_missing_ticket_returns_404(
    client: TestClient,
) -> None:
    """Creating a subtask requires an existing parent ticket."""
    response = client.post(
        f"/api/v1/tickets/{uuid4()}/subtasks",
        json={"title": "Orphan subtask"},
    )

    assert response.status_code == 404


def test_ticket_detail_can_include_subtasks(
    client: TestClient, store: InMemoryStore
) -> None:
    """GET /tickets/{id}?include=subtasks adds the checklist array."""
    ticket = _create_ticket(client, store)
    ticket_id = str(ticket["id"])
    _create_subtask(client, ticket_id, "First subtask")
    _create_subtask(client, ticket_id, "Second subtask")

    response = client.get(
        f"/api/v1/tickets/{ticket_id}", params={"include": "subtasks"}
    )

    assert response.status_code == 200
    assert [subtask["title"] for subtask in response.json()["subtasks"]] == [
        "First subtask",
        "Second subtask",
    ]
