"""Ticket use cases."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from tickets_management.core.errors import ConflictError
from tickets_management.domain.enum import Priority, TicketStatus, TicketType
from tickets_management.domain.models import Ticket
from tickets_management.repositories.protocol import (
    ProjectRepository,
    SubtaskRepository,
    TicketRepository,
)
from tickets_management.schemas.ticket import TicketCreate, TicketUpdate

PRIORITY_WEIGHT: dict[Priority, int] = {
    Priority.HIGH: 0,
    Priority.MEDIUM: 1,
    Priority.LOW: 2,
}
MAX_DUE_AT = datetime.max.replace(tzinfo=UTC)


def _sort_key(ticket: Ticket) -> tuple[int, datetime]:
    """Sort by priority descending and due date ascending."""
    return (PRIORITY_WEIGHT[ticket.priority], ticket.due_at or MAX_DUE_AT)


class TicketService:
    """Business rules for ticket management."""

    def __init__(
        self,
        tickets: TicketRepository,
        projects: ProjectRepository,
        subtasks: SubtaskRepository,
    ) -> None:
        self._tickets = tickets
        self._projects = projects
        self._subtasks = subtasks

    def list(
        self,
        *,
        project_id: UUID | None = None,
        ticket_type: TicketType | None = None,
        priority: Priority | None = None,
        status: TicketStatus | None = None,
    ) -> list[Ticket]:
        """Return tickets matching every provided filter, ordered by business rules."""
        tickets = [
            ticket
            for ticket in self._tickets.list()
            if (project_id is None or ticket.project_id == project_id)
            and (ticket_type is None or ticket.type == ticket_type)
            and (priority is None or ticket.priority == priority)
            and (status is None or ticket.status == status)
        ]
        return sorted(tickets, key=_sort_key)

    def get(self, ticket_id: UUID) -> Ticket:
        """Return a ticket or raise ``NotFoundError``."""
        return self._tickets.get(ticket_id)

    def create(self, payload: TicketCreate) -> Ticket:
        """Create a ticket in an existing, active project."""
        project = self._projects.get(payload.project_id)
        if not project.is_active:
            raise ConflictError(f"Project '{project.slug}' is not active")

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
        return self._tickets.add(ticket)

    def update(self, ticket_id: UUID, payload: TicketUpdate) -> Ticket:
        """Apply a partial update, enforcing the status transition rules."""
        ticket = self._tickets.get(ticket_id)
        changes = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not changes:
            return ticket

        new_status = changes.get("status")
        if new_status == TicketStatus.DONE:
            self._ensure_no_pending_subtasks(ticket_id)

        changes["updated_at"] = datetime.now(UTC)
        updated = self._tickets.update(replace(ticket, **changes))

        if (
            new_status in {TicketStatus.DONE, TicketStatus.CLOSED}
            and new_status != ticket.status
        ):
            self._cancel_active_reminders(ticket_id)
        return updated

    def delete(self, ticket_id: UUID) -> None:
        """Delete a ticket and its subtasks."""
        self._tickets.get(ticket_id)

        for subtask in self._subtasks.list():
            if subtask.ticket_id == ticket_id:
                self._subtasks.delete(subtask.id)

        # TODO(phase-5): delete or cancel the ticket reminders.
        self._tickets.delete(ticket_id)

    def _ensure_no_pending_subtasks(self, ticket_id: UUID) -> None:
        """Raise ``ConflictError`` when the ticket still has pending subtasks."""
        pending = sum(
            1
            for subtask in self._subtasks.list()
            if subtask.ticket_id == ticket_id and not subtask.is_done
        )
        if pending:
            raise ConflictError(
                f"Ticket has {pending} pending subtask(s); "
                "complete them before marking it as done"
            )

    def _cancel_active_reminders(self, ticket_id: UUID) -> None:
        """Cancel the active reminders of a ticket.

        TODO(phase-5): replace this placeholder with the reminders repository
        once the reminder persistence layer exists.
        """
