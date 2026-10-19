"""In-memory repository implementations.

The store keeps every entity in a ``dict`` guarded by a shared lock and hands
out copies so callers cannot mutate the stored state.
"""

from copy import deepcopy
from threading import Lock
from uuid import UUID

from tickets_management.domain.models import BaseEntity, Project, Subtask, Ticket
from tickets_management.repositories.errors import ConflictError, NotFoundError
from tickets_management.repositories.protocol import (
    ProjectRepository,
    SubtaskRepository,
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


class InMemorySubtaskRepository(_InMemoryRepository[Subtask]):
    """In-memory implementation of ``SubtaskRepository``."""


class InMemoryStore:
    """Holds the in-memory repositories sharing one lock per store."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._projects: dict[UUID, Project] = {}
        self._tickets: dict[UUID, Ticket] = {}
        self._subtasks: dict[UUID, Subtask] = {}

        self.projects: ProjectRepository = InMemoryProjectRepository(
            self._projects, self._lock
        )
        self.tickets: TicketRepository = InMemoryTicketRepository(
            self._tickets, self._lock
        )
        self.subtasks: SubtaskRepository = InMemorySubtaskRepository(
            self._subtasks, self._lock
        )
