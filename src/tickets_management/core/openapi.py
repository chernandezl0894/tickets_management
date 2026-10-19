"""OpenAPI metadata and response documentation helpers."""

from typing import Any

from fastapi import FastAPI

from tickets_management.core.errors import PROBLEM_MEDIA_TYPE, ProblemDetail

API_SUMMARY = "API REST para gestionar proyectos, tickets y subtareas."

API_DESCRIPTION = """
## Descripción

Esta API centraliza proyectos de distintas plataformas y permite gestionar sus
tickets, prioridades, fechas límite y subtareas desde un único lugar.

### Capacidades principales

- CRUD de **proyectos** con control de `slug` único y borrado en cascada.
- CRUD de **tickets** con filtros, prioridades y reglas de transición de estado.
- **Subtareas** anidadas con posición automática y reordenamiento.
- Errores consistentes basados en **RFC 9457** con el media type
  `application/problem+json`.

### Códigos de error

| Código | Significado |
|---|---|
| `404` | El recurso solicitado no existe. |
| `409` | La operación entra en conflicto con el estado actual. |
| `422` | La solicitud contiene parámetros o campos inválidos. |
| `500` | Ocurrió un error interno inesperado. |

### Documentación interactiva

- [Swagger UI](/docs)
- [ReDoc](/redoc)
- [Esquema OpenAPI](/openapi.json)
"""

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "projects",
        "description": (
            "Registro y administración de proyectos. Cada proyecto define la "
            "plataforma, el repositorio y el estado que comparten sus tickets."
        ),
    },
    {
        "name": "tickets",
        "description": (
            "Gestión de tickets, filtros, prioridades, fechas límite y reglas "
            "de transición de estado."
        ),
    },
    {
        "name": "subtasks",
        "description": (
            "Checklist anidada de cada ticket. Las subtareas se ordenan por "
            "posición y se eliminan junto con su ticket."
        ),
    },
    {
        "name": "root",
        "description": "Información básica de la API y enlace a su documentación.",
    },
    {
        "name": "health",
        "description": "Estado operativo del servicio.",
    },
]


def problem_response(description: str) -> dict[str, Any]:
    """Return an OpenAPI response documenting an RFC 9457 problem."""
    return {"description": description, "model": ProblemDetail}


def problem_responses(
    *,
    not_found: str = "No se encontró el recurso solicitado.",
    conflict: str = "La operación entra en conflicto con el estado actual.",
    validation: str = "La solicitud contiene parámetros o campos inválidos.",
    internal: str = "Ocurrió un error interno inesperado.",
) -> dict[int | str, dict[str, Any]]:
    """Build the standard error responses shared by every endpoint."""
    return {
        404: problem_response(not_found),
        409: problem_response(conflict),
        422: problem_response(validation),
        500: problem_response(internal),
    }


class DocumentedFastAPI(FastAPI):
    """FastAPI application exposing RFC 9457 responses with their media type."""

    def openapi(self) -> dict[str, Any]:
        """Generate the OpenAPI document and normalize problem responses."""
        if self.openapi_schema is not None:
            return self.openapi_schema

        schema = super().openapi()
        for path_item in schema.get("paths", {}).values():
            for operation in path_item.values():
                for response in operation.get("responses", {}).values():
                    content = response.get("content")
                    if not isinstance(content, dict):
                        continue
                    json_content = content.get("application/json")
                    if _is_problem_content(json_content):
                        content[PROBLEM_MEDIA_TYPE] = content.pop("application/json")

        self.openapi_schema = schema
        return schema


def _is_problem_content(content: object) -> bool:
    """Return whether an OpenAPI content entry references ProblemDetail."""
    if not isinstance(content, dict):
        return False
    schema = content.get("schema")
    return (
        isinstance(schema, dict)
        and schema.get("$ref") == "#/components/schemas/ProblemDetail"
    )
