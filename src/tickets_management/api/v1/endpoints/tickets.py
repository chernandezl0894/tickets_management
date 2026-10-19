"""Ticket API endpoints."""

from typing import Any

from fastapi import APIRouter, status

from tickets_management.domain.models import Ticket
from tickets_management.schemas.ticket import TicketCreate, TicketRead

COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
}

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    responses=COMMON_RESPONSES,
)


@router.get("", response_model=list[TicketRead], summary="List tickets")
def list_tickets() -> list[TicketRead]:
    """Return the tickets registered in the system."""
    return []


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create ticket",
)
def create_ticket(payload: TicketCreate) -> TicketRead:
    """Validate the payload and return the created ticket."""
    ticket = Ticket(
        project_id=payload.project_id,
        type=payload.type,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=payload.status,
        external_ref=payload.external_ref,
        due_at=payload.due_at,
    )
    return TicketRead.model_validate(ticket)
