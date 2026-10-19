"""Tests for the RFC 9457 problem details error responses."""

import logging
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from tickets_management.core.errors import register_exception_handlers


def _assert_problem(response: Response) -> dict[str, object]:
    """Assert the common problem details structure and return the payload."""
    assert response.headers["content-type"].startswith("application/problem+json")
    body: dict[str, object] = response.json()
    assert {"type", "title", "status", "detail", "instance"} <= set(body)
    return body


def test_not_found_returns_problem_details(client: TestClient) -> None:
    """A missing resource returns a 404 problem details payload."""
    project_id = uuid4()

    response = client.get(f"/api/v1/projects/{project_id}")

    assert response.status_code == 404
    body = _assert_problem(response)
    assert body["status"] == 404
    assert body["instance"] == f"/api/v1/projects/{project_id}"


def test_conflict_returns_problem_details(client: TestClient) -> None:
    """A business conflict returns a 409 problem details payload."""
    payload = {
        "name": "Tickets",
        "slug": "tickets",
        "platform": "github",
        "repo_url": "https://github.com/example/tickets",
    }
    assert client.post("/api/v1/projects", json=payload).status_code == 201

    response = client.post("/api/v1/projects", json=payload)

    assert response.status_code == 409
    body = _assert_problem(response)
    assert body["status"] == 409


def test_validation_errors_list_invalid_fields(client: TestClient) -> None:
    """A validation error returns 422 with the invalid field locations."""
    response = client.post(
        "/api/v1/tickets",
        json={
            "project_id": str(uuid4()),
            "type": "feature",
            "title": "abcd",
        },
    )

    assert response.status_code == 422
    body = _assert_problem(response)
    assert body["status"] == 422
    errors = body["errors"]
    assert isinstance(errors, list)
    first_error = errors[0]
    assert first_error["loc"] == ["body", "title"]
    assert isinstance(first_error["msg"], str)
    assert isinstance(first_error["type"], str)


def test_unhandled_exception_is_logged_without_leaking_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unexpected error returns a generic 500 and is logged."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    with (
        caplog.at_level(logging.ERROR, logger="tickets_management.core.errors"),
        TestClient(app, raise_server_exceptions=False) as test_client,
    ):
        response = test_client.get("/boom")

    assert response.status_code == 500
    body = _assert_problem(response)
    assert body["status"] == 500
    assert "secret internal detail" not in response.text
    assert "RuntimeError" in caplog.text
    assert "secret internal detail" in caplog.text
