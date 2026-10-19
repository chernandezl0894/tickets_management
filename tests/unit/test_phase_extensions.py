"""Tests for ticket search, history, and project summaries."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def _create_project(client: TestClient, slug: str = "extensions") -> dict[str, object]:
    """Create a project and return the response payload."""
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Extensions",
            "slug": slug,
            "platform": "github",
            "repo_url": f"https://github.com/example/{slug}",
        },
    )
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def _create_ticket(
    client: TestClient,
    project_id: object,
    title: str,
    description: str = "Ticket description",
) -> dict[str, object]:
    """Create a ticket and return the response payload."""
    response = client.post(
        "/api/v1/tickets",
        json={
            "project_id": str(project_id),
            "type": "feature",
            "title": title,
            "description": description,
        },
    )
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def _due_in(days: int) -> str:
    """Return an ISO due date in the future."""
    due_at = datetime.now(UTC) + timedelta(days=days)
    return due_at.isoformat().replace("+00:00", "Z")


def test_search_matches_title_and_description_case_insensitively(
    client: TestClient,
) -> None:
    """The q filter searches both fields without case sensitivity."""
    project = _create_project(client)
    _create_ticket(
        client,
        project["id"],
        "Login flow",
        "Add the authentication screen",
    )
    _create_ticket(
        client,
        project["id"],
        "Session timeout",
        "Improve the LOGIN retry behaviour",
    )
    _create_ticket(
        client,
        project["id"],
        "Billing export",
        "Download invoices as CSV",
    )

    response = client.get("/api/v1/tickets", params={"q": "LoGiN"})

    assert response.status_code == 200
    assert [ticket["title"] for ticket in response.json()] == [
        "Login flow",
        "Session timeout",
    ]


def test_search_combines_with_other_filters(client: TestClient) -> None:
    """The text query can be combined with priority and status filters."""
    project = _create_project(client)
    first = _create_ticket(client, project["id"], "Login flow")
    _create_ticket(client, project["id"], "Login audit")
    assert (
        client.patch(
            f"/api/v1/tickets/{first['id']}", json={"priority": "high"}
        ).status_code
        == 200
    )

    response = client.get(
        "/api/v1/tickets",
        params={"q": "login", "priority": "high"},
    )

    assert response.status_code == 200
    assert [ticket["id"] for ticket in response.json()] == [first["id"]]


def test_history_records_status_priority_and_due_date_changes(
    client: TestClient,
) -> None:
    """PATCH records one entry per field whose value changed."""
    project = _create_project(client)
    ticket = _create_ticket(client, project["id"], "History ticket")
    due_at = _due_in(3)

    patch = client.patch(
        f"/api/v1/tickets/{ticket['id']}",
        json={
            "status": "in_progress",
            "priority": "high",
            "due_at": due_at,
        },
    )
    assert patch.status_code == 200

    response = client.get(f"/api/v1/tickets/{ticket['id']}/history")

    assert response.status_code == 200
    changes = {entry["field"]: entry for entry in response.json()}
    assert set(changes) == {"status", "priority", "due_at"}
    assert changes["status"]["old"] == "open"
    assert changes["status"]["new"] == "in_progress"
    assert changes["priority"]["old"] == "medium"
    assert changes["priority"]["new"] == "high"
    assert changes["due_at"]["old"] is None
    assert changes["due_at"]["new"] == due_at
    assert all(entry["changed_at"] for entry in changes.values())


def test_history_is_empty_for_a_new_ticket(client: TestClient) -> None:
    """A ticket without updates has an empty history."""
    project = _create_project(client)
    ticket = _create_ticket(client, project["id"], "Untouched ticket")

    response = client.get(f"/api/v1/tickets/{ticket['id']}/history")

    assert response.status_code == 200
    assert response.json() == []


def test_history_returns_404_for_missing_ticket(client: TestClient) -> None:
    """The history endpoint resolves the ticket before returning changes."""
    response = client.get(
        "/api/v1/tickets/00000000-0000-0000-0000-000000000000/history"
    )

    assert response.status_code == 404


def test_project_summary_aggregates_status_priority_and_subtasks(
    client: TestClient,
) -> None:
    """The summary counts tickets and pending subtasks for one project."""
    project = _create_project(client)
    first = _create_ticket(client, project["id"], "First ticket")
    second = _create_ticket(client, project["id"], "Second ticket")
    third = _create_ticket(client, project["id"], "Third ticket")

    assert (
        client.patch(
            f"/api/v1/tickets/{first['id']}",
            json={"priority": "high", "status": "in_progress"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/tickets/{second['id']}",
            json={"priority": "low", "status": "done"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/tickets/{third['id']}", json={"priority": "high"}
        ).status_code
        == 200
    )

    done_subtask = client.post(
        f"/api/v1/tickets/{first['id']}/subtasks",
        json={"title": "Already done", "is_done": True},
    )
    assert done_subtask.status_code == 201
    pending_subtask = client.post(
        f"/api/v1/tickets/{first['id']}/subtasks",
        json={"title": "Still pending"},
    )
    assert pending_subtask.status_code == 201
    assert (
        client.post(
            f"/api/v1/tickets/{second['id']}/subtasks",
            json={"title": "Pending in done ticket"},
        ).status_code
        == 201
    )

    response = client.get(f"/api/v1/projects/{project['id']}/summary")

    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 3
    assert summary["by_status"]["open"] == 1
    assert summary["by_status"]["in_progress"] == 1
    assert summary["by_status"]["done"] == 1
    assert summary["by_status"]["blocked"] == 0
    assert summary["by_priority"]["high"] == 2
    assert summary["by_priority"]["medium"] == 0
    assert summary["by_priority"]["low"] == 1
    assert summary["pending_subtasks"] == 2


def test_project_summary_returns_404_for_missing_project(
    client: TestClient,
) -> None:
    """The summary endpoint returns 404 when the project does not exist."""
    response = client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/summary"
    )

    assert response.status_code == 404
