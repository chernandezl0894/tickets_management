"""Output schema for ticket change history."""

from datetime import datetime

from pydantic import ConfigDict, Field

from tickets_management.schemas.base import Schema


class TicketHistoryRead(Schema):
    """One field change recorded for a ticket."""

    field: str = Field(
        description="Nombre del campo modificado.",
        examples=["status"],
    )
    old: str | None = Field(
        description="Valor anterior, serializado como texto.",
        examples=["open"],
    )
    new: str | None = Field(
        description="Valor nuevo, serializado como texto.",
        examples=["in_progress"],
    )
    changed_at: datetime = Field(
        description="Momento del cambio en UTC.",
        examples=["2026-01-02T08:30:00Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "status",
                "old": "open",
                "new": "in_progress",
                "changed_at": "2026-01-02T08:30:00Z",
            }
        }
    )
