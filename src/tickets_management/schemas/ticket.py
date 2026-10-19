"""Input and output schemas for tickets."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from tickets_management.domain.enum import Priority, TicketStatus, TicketType
from tickets_management.schemas.base import OptionalTitledSchema, Schema, TitledSchema
from tickets_management.schemas.subtask import SubtaskRead

DUE_AT_PAST_MESSAGE = "debe ser una fecha futura"


def _validate_future_due_at(value: datetime | None) -> datetime | None:
    """Ensure an optional due date is in the future."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    if value <= datetime.now(UTC):
        raise ValueError(DUE_AT_PAST_MESSAGE)
    return value


class TicketCreate(TitledSchema):
    """Payload accepted when creating a ticket."""

    project_id: UUID = Field(
        description="Identificador del proyecto al que pertenece el ticket.",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    type: TicketType = Field(
        description="Tipo de trabajo representado por el ticket.",
        examples=["feature"],
    )
    description: str = Field(
        default="",
        description="Descripción detallada del trabajo.",
        examples=["Añadir el flujo de autenticación OTP para usuarios de Telegram."],
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Prioridad del ticket.",
        examples=["medium"],
    )
    status: TicketStatus = Field(
        default=TicketStatus.OPEN,
        description="Estado inicial del ticket.",
        examples=["open"],
    )
    external_ref: str | None = Field(
        default=None,
        description="Referencia externa, por ejemplo el identificador del issue.",
        examples=["GH-42"],
    )
    due_at: datetime | None = Field(
        default=None,
        description="Fecha límite en formato ISO 8601. Debe estar en el futuro.",
        examples=["2030-01-01T12:00:00Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "type": "feature",
                "title": "Implementar inicio de sesión con OTP",
                "description": "Añadir el flujo de autenticación OTP para Telegram.",
                "priority": "medium",
                "status": "open",
                "external_ref": "GH-42",
                "due_at": "2030-01-01T12:00:00Z",
            }
        }
    )

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime | None) -> datetime | None:
        """Reject due dates that are not in the future."""
        return _validate_future_due_at(value)


class TicketUpdate(OptionalTitledSchema):
    """Payload accepted when partially updating a ticket."""

    type: TicketType | None = Field(
        default=None,
        description="Nuevo tipo de trabajo del ticket.",
        examples=["issue"],
    )
    description: str | None = Field(
        default=None,
        description="Nueva descripción detallada del trabajo.",
        examples=["Descripción actualizada del ticket."],
    )
    priority: Priority | None = Field(
        default=None,
        description="Nueva prioridad del ticket.",
        examples=["high"],
    )
    status: TicketStatus | None = Field(
        default=None,
        description=(
            "Nuevo estado. No se puede pasar a `done` mientras existan "
            "subtareas pendientes."
        ),
        examples=["in_progress"],
    )
    external_ref: str | None = Field(
        default=None,
        description="Nueva referencia externa del ticket.",
        examples=["GH-99"],
    )
    due_at: datetime | None = Field(
        default=None,
        description="Nueva fecha límite en formato ISO 8601, en el futuro.",
        examples=["2031-06-30T18:00:00Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "in_progress",
                "priority": "high",
            }
        }
    )

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime | None) -> datetime | None:
        """Reject due dates that are not in the future."""
        return _validate_future_due_at(value)


class TicketRead(Schema):
    """Ticket data exposed to API clients."""

    id: UUID = Field(description="Identificador único del ticket.")
    project_id: UUID = Field(description="Identificador del proyecto propietario.")
    type: TicketType = Field(description="Tipo de trabajo del ticket.")
    title: str = Field(description="Título descriptivo del ticket.")
    description: str = Field(description="Descripción detallada del trabajo.")
    priority: Priority = Field(description="Prioridad del ticket.")
    status: TicketStatus = Field(description="Estado actual del ticket.")
    external_ref: str | None = Field(description="Referencia externa opcional.")
    due_at: datetime | None = Field(description="Fecha límite opcional en UTC.")
    created_at: datetime = Field(description="Fecha de creación en UTC.")
    updated_at: datetime = Field(description="Fecha de la última actualización en UTC.")
    subtasks: list[SubtaskRead] | None = Field(
        default=None,
        description=(
            "Subtareas del ticket. Solo se incluyen cuando la consulta usa "
            "`include=subtasks`."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "type": "feature",
                "title": "Implementar inicio de sesión con OTP",
                "description": "Añadir el flujo de autenticación OTP para Telegram.",
                "priority": "high",
                "status": "in_progress",
                "external_ref": "GH-42",
                "due_at": "2030-01-01T12:00:00Z",
                "created_at": "2026-01-01T12:00:00Z",
                "updated_at": "2026-01-02T08:30:00Z",
                "subtasks": [],
            }
        }
    )
