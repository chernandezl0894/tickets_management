"""Ticket API endpoints."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status

from tickets_management.api.deps import (
    TicketDep,
    TicketFilterDep,
    get_subtask_service,
    get_ticket_service,
)
from tickets_management.core.openapi import problem_responses
from tickets_management.schemas.subtask import SubtaskRead
from tickets_management.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from tickets_management.services.subtasks import SubtaskService
from tickets_management.services.tickets import TicketService

COMMON_RESPONSES = problem_responses(
    not_found="No se encontró el ticket o el proyecto indicado.",
    conflict="La operación infringe una regla de negocio del ticket.",
)

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    responses=COMMON_RESPONSES,
)


@router.get(
    "",
    response_model=list[TicketRead],
    summary="Listar tickets",
    description=(
        "Devuelve los tickets que cumplen los filtros opcionales. Los "
        "resultados se ordenan por prioridad descendente (`high`, `medium`, "
        "`low`) y, dentro de cada prioridad, por fecha límite ascendente. Los "
        "tickets sin fecha límite se colocan al final."
    ),
)
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
    summary="Crear ticket",
    description=(
        "Crea un ticket dentro de un proyecto activo. Los valores por defecto "
        "son prioridad `medium` y estado `open`. La fecha límite, si se envía, "
        "debe estar en el futuro. Responde `404` si el proyecto no existe y "
        "`409` si está inactivo."
    ),
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
    summary="Obtener ticket",
    description=(
        "Devuelve un ticket por su identificador. Usa `include=subtasks` para "
        "añadir el checklist completo del ticket a la respuesta."
    ),
)
def get_ticket(
    ticket: TicketDep,
    subtask_service: Annotated[SubtaskService, Depends(get_subtask_service)],
    include: Annotated[
        Literal["subtasks"] | None,
        Query(
            description="Incluye las subtareas del ticket cuando vale `subtasks`.",
            examples=["subtasks"],
        ),
    ] = None,
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
    summary="Actualizar ticket",
    description=(
        "Actualiza parcialmente un ticket. Solo se modifican los campos "
        "enviados. No se puede pasar a `done` mientras existan subtareas "
        "pendientes; en ese caso responde `409`."
    ),
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
    summary="Eliminar ticket",
    description=(
        "Elimina un ticket y todas sus subtareas. La operación es "
        "irreversible y responde `204` sin cuerpo."
    ),
)
def delete_ticket(
    ticket: TicketDep,
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> None:
    """Delete a ticket and its subtasks."""
    service.delete(ticket.id)
