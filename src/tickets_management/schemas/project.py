"""Input and output schemas for projects."""

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field, HttpUrl

from tickets_management.domain.enum import Platform
from tickets_management.schemas.base import Schema

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class ProjectCreate(Schema):
    """Payload accepted when registering a project."""

    name: str = Field(
        description="Nombre visible del proyecto.",
        examples=["Tickets Management"],
    )
    slug: str = Field(
        pattern=SLUG_PATTERN,
        description=(
            "Identificador URL único, en minúsculas y separado por guiones. "
            "No puede repetirse entre proyectos."
        ),
        examples=["tickets-management"],
    )
    platform: Platform = Field(
        description="Plataforma de origen del repositorio.",
        examples=["github"],
    )
    repo_url: HttpUrl = Field(
        description="URL pública del repositorio o espacio de trabajo.",
        examples=["https://github.com/example/tickets-management"],
    )
    description: str = Field(
        default="",
        description="Descripción libre del proyecto.",
        examples=["Servicio centralizado de gestión de tickets."],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tickets Management",
                "slug": "tickets-management",
                "platform": "github",
                "repo_url": "https://github.com/example/tickets-management",
                "description": "Servicio centralizado de gestión de tickets.",
            }
        }
    )


class ProjectUpdate(Schema):
    """Payload accepted when partially updating a project."""

    name: str | None = Field(
        default=None,
        description="Nuevo nombre visible del proyecto.",
        examples=["Tickets Management Renombrado"],
    )
    slug: str | None = Field(
        default=None,
        pattern=SLUG_PATTERN,
        description="Nuevo identificador URL único del proyecto.",
        examples=["tickets-management-v2"],
    )
    platform: Platform | None = Field(
        default=None,
        description="Nueva plataforma de origen.",
        examples=["gitlab"],
    )
    repo_url: HttpUrl | None = Field(
        default=None,
        description="Nueva URL del repositorio.",
        examples=["https://gitlab.com/example/tickets-management"],
    )
    description: str | None = Field(
        default=None,
        description="Nueva descripción libre del proyecto.",
        examples=["Descripción actualizada del proyecto."],
    )
    is_active: bool | None = Field(
        default=None,
        description=(
            "Indica si el proyecto admite nuevos tickets. Al desactivarlo, "
            "los tickets existentes se conservan."
        ),
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tickets Management Renombrado",
                "is_active": False,
            }
        }
    )


class ProjectRead(Schema):
    """Project data exposed to API clients."""

    id: UUID = Field(description="Identificador único del proyecto.")
    name: str = Field(description="Nombre visible del proyecto.")
    slug: str = Field(description="Identificador URL único del proyecto.")
    platform: Platform = Field(description="Plataforma de origen.")
    repo_url: HttpUrl = Field(description="URL del repositorio.")
    description: str = Field(description="Descripción libre del proyecto.")
    is_active: bool = Field(description="Indica si el proyecto admite nuevos tickets.")
    created_at: datetime = Field(description="Fecha de creación en UTC.")
    updated_at: datetime = Field(description="Fecha de la última actualización en UTC.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "Tickets Management",
                "slug": "tickets-management",
                "platform": "github",
                "repo_url": "https://github.com/example/tickets-management",
                "description": "Servicio centralizado de gestión de tickets.",
                "is_active": True,
                "created_at": "2026-01-01T12:00:00Z",
                "updated_at": "2026-01-01T12:00:00Z",
            }
        }
    )


class ProjectList(Schema):
    """Paginated list of projects."""

    items: list[ProjectRead] = Field(description="Proyectos de la página actual.")
    total: int = Field(description="Número total de proyectos registrados.")


class ProjectSummary(Schema):
    """Ticket counters for one project."""

    total: int = Field(description="Número total de tickets del proyecto.")
    by_status: dict[str, int] = Field(
        description="Número de tickets agrupados por estado.",
        examples=[{"open": 2, "in_progress": 1, "done": 3}],
    )
    by_priority: dict[str, int] = Field(
        description="Número de tickets agrupados por prioridad.",
        examples=[{"high": 2, "medium": 3, "low": 1}],
    )
    pending_subtasks: int = Field(
        description="Subtareas sin completar de todos los tickets del proyecto.",
        examples=[4],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 6,
                "by_status": {
                    "open": 2,
                    "in_progress": 1,
                    "blocked": 0,
                    "done": 3,
                    "closed": 0,
                },
                "by_priority": {"high": 2, "medium": 3, "low": 1},
                "pending_subtasks": 4,
            }
        }
    )
