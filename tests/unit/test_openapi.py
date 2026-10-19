"""Tests for the public OpenAPI contract."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tickets_management.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORTED_OPENAPI = PROJECT_ROOT / "docs" / "openapi.json"
BUSINESS_TAGS = {"projects", "tickets", "subtasks"}
PROBLEM_MEDIA_TYPE = "application/problem+json"


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    """Return the generated OpenAPI schema."""
    return app.openapi()


def test_openapi_metadata_is_complete(schema: dict[str, Any]) -> None:
    """The public document exposes the expected API metadata."""
    info = schema["info"]

    assert info["title"] == "Tickets Management API"
    assert info["summary"]
    assert "RFC 9457" in info["description"]
    assert info["version"] == "0.0.1"
    assert info["contact"]["url"].startswith("https://github.com/")
    assert info["license"]["name"] == "MIT"


def test_openapi_tags_are_described(schema: dict[str, Any]) -> None:
    """Every documented tag has a readable description."""
    tags = {tag["name"]: tag for tag in schema["tags"]}

    assert tags.keys() >= BUSINESS_TAGS
    assert all(tag.get("description") for tag in tags.values())


def test_business_operations_document_errors_and_descriptions(
    schema: dict[str, Any],
) -> None:
    """Every business operation documents the shared problem responses."""
    for path, path_item in schema["paths"].items():
        if not path.startswith("/api/v1/"):
            continue
        for method, operation in path_item.items():
            if method not in {"get", "post", "patch", "delete"}:
                continue

            assert operation.get("summary")
            assert operation.get("description")
            assert set(operation["tags"]) <= BUSINESS_TAGS

            for status_code in ("404", "409", "422"):
                response = operation["responses"][status_code]
                content = response["content"][PROBLEM_MEDIA_TYPE]
                assert content["schema"] == {
                    "$ref": "#/components/schemas/ProblemDetail"
                }


def test_problem_detail_is_a_reusable_component(schema: dict[str, Any]) -> None:
    """ProblemDetail is documented with fields and an example."""
    problem = schema["components"]["schemas"]["ProblemDetail"]

    assert {"type", "title", "status", "detail", "instance"} <= set(
        problem["properties"]
    )
    assert problem["example"]["status"] == 404


def test_request_schemas_include_examples(schema: dict[str, Any]) -> None:
    """Create and update payloads expose examples in Swagger UI."""
    components = schema["components"]["schemas"]

    for name in (
        "ProjectCreate",
        "ProjectUpdate",
        "TicketCreate",
        "TicketUpdate",
        "SubtaskCreate",
        "SubtaskUpdate",
    ):
        assert components[name]["example"]


def test_openapi_endpoint_publishes_problem_media_type(
    client: TestClient,
) -> None:
    """The runtime schema serves RFC 9457 responses with their media type."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/api/v1/tickets"]["get"]
    assert PROBLEM_MEDIA_TYPE in operation["responses"]["404"]["content"]


def test_swagger_and_redoc_render(client: TestClient) -> None:
    """Both interactive documentation pages are available."""
    swagger = client.get("/docs")
    redoc = client.get("/redoc")

    assert swagger.status_code == 200
    assert "swagger" in swagger.text.lower()
    assert redoc.status_code == 200
    assert "redoc" in redoc.text.lower()


def test_exported_openapi_is_up_to_date() -> None:
    """The committed schema matches the application definition."""
    exported = json.loads(EXPORTED_OPENAPI.read_text(encoding="utf-8"))

    assert exported == app.openapi()
