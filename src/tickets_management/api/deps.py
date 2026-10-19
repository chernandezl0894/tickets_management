"""Shared FastAPI dependencies."""

from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query

from tickets_management.core.errors import NotFoundError
from tickets_management.domain.enum import Priority, TicketStatus, TicketType
from tickets_management.domain.models import Subtask, Ticket
from tickets_management.repositories.memory import InMemoryStore
from tickets_management.repositories.protocol import (
    ProjectRepository,
    SubtaskRepository,
    TicketRepository,
)
from tickets_management.services.projects import ProjectService
from tickets_management.services.subtasks import SubtaskService
from tickets_management.services.tickets import TicketService


class Pagination:
    """Pagination query parameters shared by list endpoints."""

    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> None:
        self.limit = limit
        self.offset = offset


class TicketFilter:
    """Optional ticket filters built from query parameters."""

    def __init__(
        self,
        project_id: Annotated[UUID | None, Query()] = None,
        type: Annotated[TicketType | None, Query()] = None,
        priority: Annotated[Priority | None, Query()] = None,
        status: Annotated[TicketStatus | None, Query()] = None,
    ) -> None:
        self.project_id = project_id
        self.type = type
        self.priority = priority
        self.status = status


@lru_cache
def get_store() -> InMemoryStore:
    """Return the process-wide in-memory store."""
    return InMemoryStore()


def get_project_repository(
    store: Annotated[InMemoryStore, Depends(get_store)],
) -> ProjectRepository:
    """Return the project repository from the current store."""
    return store.projects


def get_ticket_repository(
    store: Annotated[InMemoryStore, Depends(get_store)],
) -> TicketRepository:
    """Return the ticket repository from the current store."""
    return store.tickets


def get_subtask_repository(
    store: Annotated[InMemoryStore, Depends(get_store)],
) -> SubtaskRepository:
    """Return the subtask repository from the current store."""
    return store.subtasks


def get_project_service(
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    tickets: Annotated[TicketRepository, Depends(get_ticket_repository)],
    subtasks: Annotated[SubtaskRepository, Depends(get_subtask_repository)],
) -> ProjectService:
    """Build the project service from the current repositories."""
    return ProjectService(projects, tickets, subtasks)


def get_ticket_service(
    tickets: Annotated[TicketRepository, Depends(get_ticket_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    subtasks: Annotated[SubtaskRepository, Depends(get_subtask_repository)],
) -> TicketService:
    """Build the ticket service from the current repositories."""
    return TicketService(tickets, projects, subtasks)


def get_subtask_service(
    subtasks: Annotated[SubtaskRepository, Depends(get_subtask_repository)],
    tickets: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> SubtaskService:
    """Build the subtask service from the current repositories."""
    return SubtaskService(subtasks, tickets)


def get_ticket_or_404(
    ticket_id: UUID,
    tickets: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> Ticket:
    """Return a ticket by id or raise ``NotFoundError``."""
    try:
        return tickets.get(ticket_id)
    except NotFoundError as exc:
        raise NotFoundError(f"Ticket with id {ticket_id} not found") from exc


def get_subtask_or_404(
    subtask_id: UUID,
    ticket: Annotated[Ticket, Depends(get_ticket_or_404)],
    subtasks: Annotated[SubtaskRepository, Depends(get_subtask_repository)],
) -> Subtask:
    """Return a subtask owned by the ticket or raise ``NotFoundError``."""
    subtask = subtasks.get(subtask_id)
    if subtask.ticket_id != ticket.id:
        raise NotFoundError(
            f"Subtask with id {subtask_id} not found for ticket {ticket.id}"
        )
    return subtask


PaginationDep = Annotated[Pagination, Depends()]
TicketFilterDep = Annotated[TicketFilter, Depends()]
TicketDep = Annotated[Ticket, Depends(get_ticket_or_404)]
SubtaskDep = Annotated[Subtask, Depends(get_subtask_or_404)]
