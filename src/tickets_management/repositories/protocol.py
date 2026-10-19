"""Repository contracts for the domain entities.

The protocols define the data contract of the application: which operations
exist, their signatures, and what they return. Concrete implementations must
satisfy these protocols structurally.
"""

from typing import Protocol
from uuid import UUID

from tickets_management.domain.models import (
    BaseEntity,
    Project,
    Subtask,
    Ticket,
    TicketHistory,
)


class Repository[T: BaseEntity](Protocol):
    """Generic CRUD contract for a domain entity."""

    def list(self) -> list[T]:
        """Return every stored entity."""
        ...

    def get(self, entity_id: UUID) -> T:
        """Return the entity with ``entity_id`` or raise ``NotFoundError``."""
        ...

    def add(self, entity: T) -> T:
        """Store a new entity and return it."""
        ...

    def update(self, entity: T) -> T:
        """Replace an existing entity and return it."""
        ...

    def delete(self, entity_id: UUID) -> None:
        """Delete the entity with ``entity_id``."""
        ...


class ProjectRepository(Repository[Project], Protocol):
    """Data operations for projects."""


class TicketRepository(Repository[Ticket], Protocol):
    """Data operations for tickets."""

    def search(self, query: str) -> list[Ticket]:
        """Return tickets whose title or description contains ``query``."""
        ...

    def list_by_project(self, project_id: UUID) -> list[Ticket]:
        """Return the tickets that belong to ``project_id``."""
        ...


class SubtaskRepository(Repository[Subtask], Protocol):
    """Data operations for subtasks."""

    def count_pending_by_ticket_ids(self, ticket_ids: set[UUID]) -> int:
        """Count unfinished subtasks belonging to any of ``ticket_ids``."""
        ...


class TicketHistoryRepository(Repository[TicketHistory], Protocol):
    """Data operations for ticket change history."""

    def list_for_ticket(self, ticket_id: UUID) -> list[TicketHistory]:
        """Return the changes recorded for ``ticket_id`` in chronological order."""
        ...
