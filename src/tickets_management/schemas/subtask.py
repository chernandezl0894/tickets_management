"""Input and output schemas for subtasks."""

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from tickets_management.schemas.base import (
    OptionalTitledSchema,
    Schema,
    TitledSchema,
)


class SubtaskCreate(TitledSchema):
    """Payload accepted when creating a subtask inside a ticket."""

    is_done: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Write integration tests",
                "is_done": False,
            }
        }
    )


class SubtaskUpdate(OptionalTitledSchema):
    """Payload accepted when partially updating a subtask."""

    is_done: bool | None = None


class SubtaskRead(Schema):
    """Subtask data exposed to API clients."""

    id: UUID
    ticket_id: UUID
    title: str
    is_done: bool
    position: int
    created_at: datetime
    updated_at: datetime
