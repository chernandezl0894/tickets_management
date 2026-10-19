"""Input and output schemas for tickets."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import ConfigDict, field_validator

from tickets_management.domain.enum import Priority, TicketStatus, TicketType
from tickets_management.schemas.base import OptionalTitledSchema, Schema, TitledSchema

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

    project_id: UUID
    type: TicketType
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    external_ref: str | None = None
    due_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "type": "feature",
                "title": "Implement Telegram OTP login",
                "description": "Add the OTP authentication flow for Telegram users.",
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

    type: TicketType | None = None
    description: str | None = None
    priority: Priority | None = None
    status: TicketStatus | None = None
    external_ref: str | None = None
    due_at: datetime | None = None

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime | None) -> datetime | None:
        """Reject due dates that are not in the future."""
        return _validate_future_due_at(value)


class TicketRead(Schema):
    """Ticket data exposed to API clients."""

    id: UUID
    project_id: UUID
    type: TicketType
    title: str
    description: str
    priority: Priority
    status: TicketStatus
    external_ref: str | None
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime
