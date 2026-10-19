"""Repository contracts for the domain entities.

The protocols define the data contract of the application: which operations
exist, their signatures, and what they return. Concrete implementations must
satisfy these protocols structurally.
"""

from typing import Protocol
from uuid import UUID

from tickets_management.domain.models import BaseEntity, Project, Subtask, Ticket


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


class SubtaskRepository(Repository[Subtask], Protocol):
    """Data operations for subtasks."""
