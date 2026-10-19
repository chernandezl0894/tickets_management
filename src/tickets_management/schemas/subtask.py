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
    """Payload accepted when creating a subtask."""

    ticket_id: UUID
    is_done: bool = False
    position: int = 0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticket_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "title": "Write integration tests",
                "is_done": False,
                "position": 0,
            }
        }
    )


class SubtaskUpdate(OptionalTitledSchema):
    """Payload accepted when partially updating a subtask."""

    is_done: bool | None = None
    position: int | None = None


class SubtaskRead(Schema):
    """Subtask data exposed to API clients."""

    id: UUID
    ticket_id: UUID
    title: str
    is_done: bool
    position: int
    created_at: datetime
    updated_at: datetime
