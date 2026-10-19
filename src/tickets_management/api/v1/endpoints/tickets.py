"""Ticket API endpoints."""

from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from tickets_management.api.deps import get_subtask_service, get_ticket_service
from tickets_management.domain.enum import Priority, TicketStatus, TicketType
from tickets_management.schemas.subtask import (
    SubtaskCreate,
    SubtaskRead,
    SubtaskUpdate,
)
from tickets_management.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from tickets_management.services.subtasks import SubtaskService
from tickets_management.services.tickets import TicketService

COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
}
NOT_FOUND_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"description": "Ticket not found"},
}
CONFLICT_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {"description": "Business rule conflict"},
}

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    responses=COMMON_RESPONSES,
)


@router.get("", response_model=list[TicketRead], summary="List tickets")
def list_tickets(
    service: Annotated[TicketService, Depends(get_ticket_service)],
    project_id: Annotated[UUID | None, Query()] = None,
    type: Annotated[TicketType | None, Query()] = None,
    priority: Annotated[Priority | None, Query()] = None,
    status: Annotated[TicketStatus | None, Query()] = None,
) -> list[TicketRead]:
    """Return tickets filtered and ordered by the business rules."""
    tickets = service.list(
        project_id=project_id,
        ticket_type=type,
        priority=priority,
        status=status,
    )
    return [TicketRead.model_validate(ticket) for ticket in tickets]


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND_RESPONSES | CONFLICT_RESPONSES,
    summary="Create ticket",
)
def create_ticket(
    payload: TicketCreate,
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> TicketRead:
    """Create a ticket in an existing, active project."""
    return TicketRead.model_validate(service.create(payload))


@router.get(
    "/{ticket_id}",
    response_model=TicketRead,
    responses=NOT_FOUND_RESPONSES,
    summary="Get ticket",
)
def get_ticket(
    ticket_id: UUID,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    subtask_service: Annotated[SubtaskService, Depends(get_subtask_service)],
    include: Annotated[Literal["subtasks"] | None, Query()] = None,
) -> TicketRead:
    """Return a ticket by id, optionally including its subtasks."""
    ticket = TicketRead.model_validate(service.get(ticket_id))
    if include == "subtasks":
        ticket.subtasks = [
            SubtaskRead.model_validate(subtask)
            for subtask in subtask_service.list(ticket_id)
        ]
    return ticket


@router.patch(
    "/{ticket_id}",
    response_model=TicketRead,
    responses=NOT_FOUND_RESPONSES | CONFLICT_RESPONSES,
    summary="Update ticket",
)
def update_ticket(
    ticket_id: UUID,
    payload: TicketUpdate,
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> TicketRead:
    """Partially update a ticket, enforcing the status transitions."""
    return TicketRead.model_validate(service.update(ticket_id, payload))


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND_RESPONSES,
    summary="Delete ticket",
)
def delete_ticket(
    ticket_id: UUID,
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> None:
    """Delete a ticket and its subtasks."""
    service.delete(ticket_id)


@router.get(
    "/{ticket_id}/subtasks",
    response_model=list[SubtaskRead],
    responses=NOT_FOUND_RESPONSES,
    summary="List ticket subtasks",
)
def list_ticket_subtasks(
    ticket_id: UUID,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> list[SubtaskRead]:
    """Return the ticket subtasks ordered by position."""
    return [SubtaskRead.model_validate(subtask) for subtask in service.list(ticket_id)]


@router.post(
    "/{ticket_id}/subtasks",
    response_model=SubtaskRead,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND_RESPONSES,
    summary="Create ticket subtask",
)
def create_ticket_subtask(
    ticket_id: UUID,
    payload: SubtaskCreate,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> SubtaskRead:
    """Append a subtask to the ticket checklist."""
    return SubtaskRead.model_validate(service.create(ticket_id, payload))


@router.patch(
    "/{ticket_id}/subtasks/{subtask_id}",
    response_model=SubtaskRead,
    responses=NOT_FOUND_RESPONSES,
    summary="Update ticket subtask",
)
def update_ticket_subtask(
    ticket_id: UUID,
    subtask_id: UUID,
    payload: SubtaskUpdate,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> SubtaskRead:
    """Rename or mark a ticket subtask."""
    return SubtaskRead.model_validate(service.update(ticket_id, subtask_id, payload))


@router.delete(
    "/{ticket_id}/subtasks/{subtask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND_RESPONSES,
    summary="Delete ticket subtask",
)
def delete_ticket_subtask(
    ticket_id: UUID,
    subtask_id: UUID,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> None:
    """Delete a ticket subtask and reorder the remaining positions."""
    service.delete(ticket_id, subtask_id)
