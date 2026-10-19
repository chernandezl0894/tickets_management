"""Ticket API endpoints."""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, status

from tickets_management.api.deps import (
    SubtaskDep,
    TicketDep,
    TicketFilterDep,
    get_subtask_service,
    get_ticket_service,
)
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
    filters: TicketFilterDep,
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> list[TicketRead]:
    """Return tickets filtered and ordered by the business rules."""
    tickets = service.list(
        project_id=filters.project_id,
        ticket_type=filters.type,
        priority=filters.priority,
        status=filters.status,
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
    ticket: TicketDep,
    subtask_service: Annotated[SubtaskService, Depends(get_subtask_service)],
    include: Annotated[Literal["subtasks"] | None, Query()] = None,
) -> TicketRead:
    """Return a ticket by id, optionally including its subtasks."""
    result = TicketRead.model_validate(ticket)
    if include == "subtasks":
        result.subtasks = [
            SubtaskRead.model_validate(subtask)
            for subtask in subtask_service.list(ticket.id)
        ]
    return result


@router.patch(
    "/{ticket_id}",
    response_model=TicketRead,
    responses=NOT_FOUND_RESPONSES | CONFLICT_RESPONSES,
    summary="Update ticket",
)
def update_ticket(
    ticket: TicketDep,
    payload: TicketUpdate,
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> TicketRead:
    """Partially update a ticket, enforcing the status transitions."""
    return TicketRead.model_validate(service.update(ticket.id, payload))


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND_RESPONSES,
    summary="Delete ticket",
)
def delete_ticket(
    ticket: TicketDep,
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> None:
    """Delete a ticket and its subtasks."""
    service.delete(ticket.id)


@router.get(
    "/{ticket_id}/subtasks",
    response_model=list[SubtaskRead],
    responses=NOT_FOUND_RESPONSES,
    summary="List ticket subtasks",
)
def list_ticket_subtasks(
    ticket: TicketDep,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> list[SubtaskRead]:
    """Return the ticket subtasks ordered by position."""
    return [SubtaskRead.model_validate(subtask) for subtask in service.list(ticket.id)]


@router.post(
    "/{ticket_id}/subtasks",
    response_model=SubtaskRead,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND_RESPONSES,
    summary="Create ticket subtask",
)
def create_ticket_subtask(
    ticket: TicketDep,
    payload: SubtaskCreate,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> SubtaskRead:
    """Append a subtask to the ticket checklist."""
    return SubtaskRead.model_validate(service.create(ticket.id, payload))


@router.patch(
    "/{ticket_id}/subtasks/{subtask_id}",
    response_model=SubtaskRead,
    responses=NOT_FOUND_RESPONSES,
    summary="Update ticket subtask",
)
def update_ticket_subtask(
    subtask: SubtaskDep,
    payload: SubtaskUpdate,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> SubtaskRead:
    """Rename or mark a ticket subtask."""
    return SubtaskRead.model_validate(
        service.update(subtask.ticket_id, subtask.id, payload)
    )


@router.delete(
    "/{ticket_id}/subtasks/{subtask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND_RESPONSES,
    summary="Delete ticket subtask",
)
def delete_ticket_subtask(
    subtask: SubtaskDep,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> None:
    """Delete a ticket subtask and reorder the remaining positions."""
    service.delete(subtask.ticket_id, subtask.id)
