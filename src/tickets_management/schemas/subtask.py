"""Input and output schemas for subtasks."""

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from tickets_management.schemas.base import (
    OptionalTitledSchema,
    Schema,
    TitledSchema,
)


class SubtaskCreate(TitledSchema):
    """Payload accepted when creating a subtask inside a ticket."""

    is_done: bool = Field(
        default=False,
        description="Indica si la subtarea ya está completada.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Escribir pruebas de integración",
                "is_done": False,
            }
        }
    )


class SubtaskUpdate(OptionalTitledSchema):
    """Payload accepted when partially updating a subtask."""

    is_done: bool | None = Field(
        default=None,
        description="Marca la subtarea como completada o pendiente.",
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Revisar las pruebas de integración",
                "is_done": True,
            }
        }
    )


class SubtaskRead(Schema):
    """Subtask data exposed to API clients."""

    id: UUID = Field(description="Identificador único de la subtarea.")
    ticket_id: UUID = Field(description="Identificador del ticket propietario.")
    title: str = Field(description="Título descriptivo de la subtarea.")
    is_done: bool = Field(description="Indica si la subtarea está completada.")
    position: int = Field(description="Posición de la subtarea dentro del checklist.")
    created_at: datetime = Field(description="Fecha de creación en UTC.")
    updated_at: datetime = Field(description="Fecha de la última actualización en UTC.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "9b2f4c1a-8d3e-4f5a-b6c7-d8e9f0a1b2c3",
                "ticket_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "title": "Escribir pruebas de integración",
                "is_done": False,
                "position": 0,
                "created_at": "2026-01-01T12:00:00Z",
                "updated_at": "2026-01-01T12:00:00Z",
            }
        }
    )
