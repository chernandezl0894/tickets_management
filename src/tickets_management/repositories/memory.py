"""In-memory repository implementations.

The store keeps every entity in a ``dict`` guarded by a shared lock and hands
out copies so callers cannot mutate the stored state.
"""

from copy import deepcopy
from threading import Lock
from uuid import UUID

from tickets_management.core.errors import ConflictError, NotFoundError
from tickets_management.domain.models import (
    BaseEntity,
    Project,
    Subtask,
    Ticket,
    TicketHistory,
)
from tickets_management.repositories.protocol import (
    ProjectRepository,
    SubtaskRepository,
    TicketHistoryRepository,
    TicketRepository,
)


class _InMemoryRepository[T: BaseEntity]:
    """Shared CRUD implementation backed by a ``dict`` and a lock."""

    def __init__(
        self,
        items: dict[UUID, T] | None = None,
        lock: Lock | None = None,
    ) -> None:
        self._items = items if items is not None else {}
        self._lock = lock if lock is not None else Lock()

    def list(self) -> list[T]:
        """Return copies of every stored entity."""
        with self._lock:
            return [deepcopy(entity) for entity in self._items.values()]

    def get(self, entity_id: UUID) -> T:
        """Return a copy of the entity or raise ``NotFoundError``."""
        with self._lock:
            entity = self._items.get(entity_id)
        if entity is None:
            raise NotFoundError(f"Entity with id {entity_id} not found")
        return deepcopy(entity)

    def add(self, entity: T) -> T:
        """Store a copy of a new entity or raise ``ConflictError``."""
        with self._lock:
            if entity.id in self._items:
                raise ConflictError(f"Entity with id {entity.id} already exists")
            self._items[entity.id] = deepcopy(entity)
        return deepcopy(entity)

    def update(self, entity: T) -> T:
        """Replace an existing entity or raise ``NotFoundError``."""
        with self._lock:
            if entity.id not in self._items:
                raise NotFoundError(f"Entity with id {entity.id} not found")
            self._items[entity.id] = deepcopy(entity)
        return deepcopy(entity)

    def delete(self, entity_id: UUID) -> None:
        """Delete an existing entity or raise ``NotFoundError``."""
        with self._lock:
            if entity_id not in self._items:
                raise NotFoundError(f"Entity with id {entity_id} not found")
            del self._items[entity_id]


class InMemoryProjectRepository(_InMemoryRepository[Project]):
    """In-memory implementation of ``ProjectRepository``."""


class InMemoryTicketRepository(_InMemoryRepository[Ticket]):
    """In-memory implementation of ``TicketRepository``."""

    def search(self, query: str) -> list[Ticket]:
        """Return tickets matching ``query`` in title or description."""
        normalized = query.casefold()
        with self._lock:
            return [
                deepcopy(ticket)
                for ticket in self._items.values()
                if normalized in ticket.title.casefold()
                or normalized in ticket.description.casefold()
            ]

    def list_by_project(self, project_id: UUID) -> list[Ticket]:
        """Return the tickets that belong to ``project_id``."""
        with self._lock:
            return [
                deepcopy(ticket)
                for ticket in self._items.values()
                if ticket.project_id == project_id
            ]


class InMemorySubtaskRepository(_InMemoryRepository[Subtask]):
    """In-memory implementation of ``SubtaskRepository``."""

    def count_pending_by_ticket_ids(self, ticket_ids: set[UUID]) -> int:
        """Count unfinished subtasks belonging to any of ``ticket_ids``."""
        with self._lock:
            return sum(
                1
                for subtask in self._items.values()
                if subtask.ticket_id in ticket_ids and not subtask.is_done
            )


class InMemoryTicketHistoryRepository(_InMemoryRepository[TicketHistory]):
    """In-memory implementation of ``TicketHistoryRepository``."""

    def list_for_ticket(self, ticket_id: UUID) -> list[TicketHistory]:
        """Return the changes recorded for ``ticket_id`` in chronological order."""
        with self._lock:
            changes = [
                deepcopy(change)
                for change in self._items.values()
                if change.ticket_id == ticket_id
            ]
        return sorted(changes, key=lambda change: change.changed_at)


class InMemoryStore:
    """Holds the in-memory repositories sharing one lock per store."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._projects: dict[UUID, Project] = {}
        self._tickets: dict[UUID, Ticket] = {}
        self._subtasks: dict[UUID, Subtask] = {}
        self._history: dict[UUID, TicketHistory] = {}

        self.projects: ProjectRepository = InMemoryProjectRepository(
            self._projects, self._lock
        )
        self.tickets: TicketRepository = InMemoryTicketRepository(
            self._tickets, self._lock
        )
        self.subtasks: SubtaskRepository = InMemorySubtaskRepository(
            self._subtasks, self._lock
        )
        self.history: TicketHistoryRepository = InMemoryTicketHistoryRepository(
            self._history, self._lock
        )
