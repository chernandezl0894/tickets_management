"""Nested ticket subtask API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from tickets_management.api.deps import (
    SubtaskDep,
    TicketDep,
    get_subtask_service,
)
from tickets_management.core.openapi import problem_responses
from tickets_management.schemas.subtask import (
    SubtaskCreate,
    SubtaskRead,
    SubtaskUpdate,
)
from tickets_management.services.subtasks import SubtaskService

COMMON_RESPONSES = problem_responses(
    not_found="No se encontró el ticket o la subtarea solicitada.",
    conflict="La operación entra en conflicto con el estado actual de la subtarea.",
)

router = APIRouter(
    prefix="/tickets",
    tags=["subtasks"],
    responses=COMMON_RESPONSES,
)


@router.get(
    "/{ticket_id}/subtasks",
    response_model=list[SubtaskRead],
    summary="Listar subtareas",
    description=(
        "Devuelve el checklist de un ticket ordenado por `position`. Responde "
        "`404` si el ticket no existe."
    ),
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
    summary="Crear subtarea",
    description=(
        "Añade una subtarea al final del checklist del ticket. La posición se "
        "asigna automáticamente. Responde `404` si el ticket no existe."
    ),
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
    summary="Actualizar subtarea",
    description=(
        "Renombra una subtarea o cambia su estado de completada. La subtarea "
        "debe pertenecer al ticket indicado; de lo contrario responde `404`."
    ),
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
    summary="Eliminar subtarea",
    description=(
        "Elimina una subtarea y reordena las posiciones restantes sin dejar "
        "huecos. Responde `404` si el ticket o la subtarea no existen."
    ),
)
def delete_ticket_subtask(
    subtask: SubtaskDep,
    service: Annotated[SubtaskService, Depends(get_subtask_service)],
) -> None:
    """Delete a ticket subtask and reorder the remaining positions."""
    service.delete(subtask.ticket_id, subtask.id)
