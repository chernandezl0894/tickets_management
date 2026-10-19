"""Tests for the API input and output schemas."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tickets_management.schemas.project import ProjectCreate, ProjectRead
from tickets_management.schemas.subtask import SubtaskCreate, SubtaskRead
from tickets_management.schemas.ticket import (
    DUE_AT_PAST_MESSAGE,
    TicketCreate,
    TicketRead,
)


def _build_app() -> FastAPI:
    """Create a minimal app that exposes the schemas through FastAPI."""
    app = FastAPI()

    @app.post("/tickets")
    def create_ticket(payload: TicketCreate) -> dict[str, str]:
        return {"project_id": str(payload.project_id)}

    @app.post("/projects")
    def create_project(payload: ProjectCreate) -> dict[str, str]:
        return {"slug": payload.slug}

    @app.post("/subtasks")
    def create_subtask(payload: SubtaskCreate) -> dict[str, str]:
        return {"ticket_id": str(payload.ticket_id)}

    return app


def test_ticket_rejects_title_with_four_characters() -> None:
    """FastAPI returns 422 when the ticket title is too short."""
    client = TestClient(_build_app())

    response = client.post(
        "/tickets",
        json={
            "project_id": str(uuid4()),
            "type": "feature",
            "title": "abcd",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


def test_title_is_trimmed_before_validation() -> None:
    """Surrounding whitespace is removed before checking the title length."""
    ticket = TicketCreate(
        project_id=uuid4(),
        type="feature",
        title="  Valid title  ",
    )

    assert ticket.title == "Valid title"


def test_project_rejects_invalid_repo_url() -> None:
    """FastAPI returns 422 and points at the repo_url field."""
    client = TestClient(_build_app())

    response = client.post(
        "/projects",
        json={
            "name": "Tickets",
            "slug": "tickets",
            "platform": "github",
            "repo_url": "not-a-url",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "repo_url"]


def test_project_rejects_slug_with_invalid_characters() -> None:
    """Slugs only accept lowercase letters, numbers, and hyphens."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            name="Tickets",
            slug="Tickets Management",
            platform="github",
            repo_url="https://github.com/example/tickets",
        )

    assert exc_info.value.errors()[0]["loc"] == ("slug",)


def test_ticket_rejects_past_due_at() -> None:
    """FastAPI returns 422 when due_at is in the past."""
    client = TestClient(_build_app())

    response = client.post(
        "/tickets",
        json={
            "project_id": str(uuid4()),
            "type": "feature",
            "title": "Valid ticket title",
            "due_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 422
    assert DUE_AT_PAST_MESSAGE in response.json()["detail"][0]["msg"]


def test_ticket_example_is_exposed_in_openapi() -> None:
    """TicketCreate exposes a ready-to-use example in /docs."""
    schema = _build_app().openapi()["components"]["schemas"]["TicketCreate"]

    assert schema["example"]["priority"] == "medium"
    assert schema["example"]["type"] == "feature"


@pytest.mark.parametrize(
    ("schema", "expected_fields"),
    [
        (
            ProjectRead,
            {
                "id",
                "name",
                "slug",
                "platform",
                "repo_url",
                "description",
                "is_active",
                "created_at",
                "updated_at",
            },
        ),
        (
            TicketRead,
            {
                "id",
                "project_id",
                "type",
                "title",
                "description",
                "priority",
                "status",
                "external_ref",
                "due_at",
                "created_at",
                "updated_at",
            },
        ),
        (
            SubtaskRead,
            {
                "id",
                "ticket_id",
                "title",
                "is_done",
                "position",
                "created_at",
                "updated_at",
            },
        ),
    ],
)
def test_read_schemas_only_expose_public_fields(
    schema: type[ProjectRead | TicketRead | SubtaskRead],
    expected_fields: set[str],
) -> None:
    """Read schemas expose exactly the fields intended for clients."""
    assert set(schema.model_fields) == expected_fields
