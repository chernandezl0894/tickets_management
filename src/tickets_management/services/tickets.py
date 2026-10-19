"""Ticket use cases."""

from dataclasses import replace
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from tickets_management.core.errors import ConflictError
from tickets_management.domain.enum import Priority, TicketStatus, TicketType
from tickets_management.domain.models import Ticket, TicketHistory
from tickets_management.repositories.protocol import (
    ProjectRepository,
    SubtaskRepository,
    TicketHistoryRepository,
    TicketRepository,
)
from tickets_management.schemas.ticket import TicketCreate, TicketUpdate

PRIORITY_WEIGHT: dict[Priority, int] = {
    Priority.HIGH: 0,
    Priority.MEDIUM: 1,
    Priority.LOW: 2,
}
MAX_DUE_AT = datetime.max.replace(tzinfo=UTC)
TicketHistoryList = list[TicketHistory]


def _sort_key(ticket: Ticket) -> tuple[int, datetime]:
    """Sort by priority descending and due date ascending."""
    return (PRIORITY_WEIGHT[ticket.priority], ticket.due_at or MAX_DUE_AT)


def _history_value(value: object) -> str | None:
    """Serialize a field value for the change history."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


class TicketService:
    """Business rules for ticket management."""

    def __init__(
        self,
        tickets: TicketRepository,
        projects: ProjectRepository,
        subtasks: SubtaskRepository,
        history: TicketHistoryRepository,
    ) -> None:
        self._tickets = tickets
        self._projects = projects
        self._subtasks = subtasks
        self._history = history

    def list(
        self,
        *,
        project_id: UUID | None = None,
        ticket_type: TicketType | None = None,
        priority: Priority | None = None,
        status: TicketStatus | None = None,
        query: str | None = None,
    ) -> list[Ticket]:
        """Return tickets matching every provided filter, ordered by business rules."""
        normalized_query = query.strip() if query else None
        tickets = (
            self._tickets.search(normalized_query)
            if normalized_query
            else self._tickets.list()
        )
        filtered = [
            ticket
            for ticket in tickets
            if (project_id is None or ticket.project_id == project_id)
            and (ticket_type is None or ticket.type == ticket_type)
            and (priority is None or ticket.priority == priority)
            and (status is None or ticket.status == status)
        ]
        return sorted(filtered, key=_sort_key)

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

        changed_at = datetime.now(UTC)
        changes["updated_at"] = changed_at
        updated = self._tickets.update(replace(ticket, **changes))
        self._record_changes(ticket, changes, changed_at=changed_at)

        if (
            new_status in {TicketStatus.DONE, TicketStatus.CLOSED}
            and new_status != ticket.status
        ):
            self._cancel_active_reminders(ticket_id)
        return updated

    def get_history(self, ticket_id: UUID) -> TicketHistoryList:
        """Return the recorded changes of a ticket in chronological order."""
        self._tickets.get(ticket_id)
        return self._history.list_for_ticket(ticket_id)

    def delete(self, ticket_id: UUID) -> None:
        """Delete a ticket and its subtasks."""
        self._tickets.get(ticket_id)

        for subtask in self._subtasks.list():
            if subtask.ticket_id == ticket_id:
                self._subtasks.delete(subtask.id)
        for change in self._history.list_for_ticket(ticket_id):
            self._history.delete(change.id)

        # TODO(phase-5): delete or cancel the ticket reminders.
        self._tickets.delete(ticket_id)

    def _record_changes(
        self,
        ticket: Ticket,
        changes: dict[str, object],
        *,
        changed_at: datetime,
    ) -> None:
        """Store one history entry per field whose value actually changed."""
        for field_name, new_value in changes.items():
            if field_name == "updated_at":
                continue
            old_value = getattr(ticket, field_name)
            if old_value == new_value:
                continue
            self._history.add(
                TicketHistory(
                    ticket_id=ticket.id,
                    field=field_name,
                    old=_history_value(old_value),
                    new=_history_value(new_value),
                    changed_at=changed_at,
                )
            )

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
