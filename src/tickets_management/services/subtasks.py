"""Subtask use cases."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from tickets_management.core.errors import NotFoundError
from tickets_management.domain.models import Subtask
from tickets_management.repositories.protocol import (
    SubtaskRepository,
    TicketRepository,
)
from tickets_management.schemas.subtask import SubtaskCreate, SubtaskUpdate


class SubtaskService:
    """Business rules for subtasks nested under a ticket."""

    def __init__(
        self,
        subtasks: SubtaskRepository,
        tickets: TicketRepository,
    ) -> None:
        self._subtasks = subtasks
        self._tickets = tickets

    def list(self, ticket_id: UUID) -> list[Subtask]:
        """Return the ticket subtasks ordered by position."""
        self._tickets.get(ticket_id)
        subtasks = [
            subtask
            for subtask in self._subtasks.list()
            if subtask.ticket_id == ticket_id
        ]
        return sorted(subtasks, key=lambda subtask: subtask.position)

    def create(self, ticket_id: UUID, payload: SubtaskCreate) -> Subtask:
        """Append a subtask to the ticket checklist."""
        self._tickets.get(ticket_id)
        existing = [
            subtask
            for subtask in self._subtasks.list()
            if subtask.ticket_id == ticket_id
        ]
        next_position = max((subtask.position for subtask in existing), default=-1) + 1
        subtask = Subtask(
            ticket_id=ticket_id,
            title=payload.title,
            is_done=payload.is_done,
            position=next_position,
        )
        return self._subtasks.add(subtask)

    def update(
        self,
        ticket_id: UUID,
        subtask_id: UUID,
        payload: SubtaskUpdate,
    ) -> Subtask:
        """Rename or mark a subtask, validating it belongs to the ticket."""
        subtask = self._get_owned_subtask(ticket_id, subtask_id)
        changes = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not changes:
            return subtask

        changes["updated_at"] = datetime.now(UTC)
        return self._subtasks.update(replace(subtask, **changes))

    def delete(self, ticket_id: UUID, subtask_id: UUID) -> None:
        """Delete a subtask and close the position gap."""
        self._get_owned_subtask(ticket_id, subtask_id)
        self._subtasks.delete(subtask_id)
        self._reorder(ticket_id)

    def _get_owned_subtask(self, ticket_id: UUID, subtask_id: UUID) -> Subtask:
        """Return a subtask that belongs to the ticket or raise NotFoundError."""
        self._tickets.get(ticket_id)
        subtask = self._subtasks.get(subtask_id)
        if subtask.ticket_id != ticket_id:
            raise NotFoundError(
                f"Subtask with id {subtask_id} not found for ticket {ticket_id}"
            )
        return subtask

    def _reorder(self, ticket_id: UUID) -> None:
        """Rewrite positions so the remaining subtasks have no gaps."""
        remaining = [
            subtask
            for subtask in self._subtasks.list()
            if subtask.ticket_id == ticket_id
        ]
        for position, subtask in enumerate(
            sorted(remaining, key=lambda item: item.position)
        ):
            if subtask.position != position:
                self._subtasks.update(replace(subtask, position=position))
