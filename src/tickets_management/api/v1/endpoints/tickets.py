"""Ticket API endpoints."""

from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from tickets_management.api.deps import get_subtask_service, get_ticket_service
from tickets_management.domain.enum import Priority, TicketStatus, TicketType
from tickets_management.repositories.errors import ConflictError, NotFoundError
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
    try:
        ticket = service.create(payload)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return TicketRead.model_validate(ticket)


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
    try:
        ticket = service.get(ticket_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    result = TicketRead.model_validate(ticket)
    if include == "subtasks":
        result.subtasks = [
            SubtaskRead.model_validate(subtask)
            for subtask in subtask_service.list(ticket_id)
        ]
    return result


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
    try:
        ticket = service.update(ticket_id, payload)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return TicketRead.model_validate(ticket)


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
    try:
        service.delete(ticket_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


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
    try:
        subtasks = service.list(ticket_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return [SubtaskRead.model_validate(subtask) for subtask in subtasks]


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
    try:
        subtask = service.create(ticket_id, payload)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return SubtaskRead.model_validate(subtask)


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
    try:
        subtask = service.update(ticket_id, subtask_id, payload)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return SubtaskRead.model_validate(subtask)


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
    try:
        service.delete(ticket_id, subtask_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
