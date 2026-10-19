"""Tests for the versioned API router structure."""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://user:password@localhost:5432/tickets_management",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from uuid import uuid4

from fastapi.testclient import TestClient

from tickets_management.main import app

client = TestClient(app)


def test_business_endpoints_are_versioned_under_api_v1() -> None:
    """All business routes live under /api/v1."""
    paths = set(app.openapi()["paths"])

    assert "/api/v1/projects" in paths
    assert "/api/v1/tickets" in paths
    assert all(
        path.startswith("/api/v1/") for path in paths if path not in {"/", "/health"}
    )


def test_docs_group_endpoints_by_resource_tag() -> None:
    """OpenAPI operations are grouped under the projects and tickets tags."""
    paths = app.openapi()["paths"]

    project_tags = {
        operation["tags"][0] for operation in paths["/api/v1/projects"].values()
    }
    ticket_tags = {
        operation["tags"][0] for operation in paths["/api/v1/tickets"].values()
    }

    assert project_tags == {"projects"}
    assert ticket_tags == {"tickets"}


def test_list_endpoints_respond_under_api_v1() -> None:
    """The list endpoints are reachable through the versioned prefix."""
    assert client.get("/api/v1/projects").status_code == 200
    assert client.get("/api/v1/tickets").status_code == 200


def test_create_endpoints_respond_under_api_v1() -> None:
    """The create endpoints are reachable through the versioned prefix."""
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "Tickets",
            "slug": "tickets",
            "platform": "github",
            "repo_url": "https://github.com/example/tickets",
        },
    )
    ticket_response = client.post(
        "/api/v1/tickets",
        json={
            "project_id": str(uuid4()),
            "type": "feature",
            "title": "Valid ticket title",
        },
    )

    assert project_response.status_code == 201
    assert ticket_response.status_code == 201


def test_health_is_not_prefixed_with_the_api_version() -> None:
    """Health remains an infrastructure route outside /api/v1."""
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 404
