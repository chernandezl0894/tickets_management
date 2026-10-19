"""Shared FastAPI dependencies."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from tickets_management.repositories.memory import InMemoryStore
from tickets_management.services.projects import ProjectService


@lru_cache
def get_store() -> InMemoryStore:
    """Return the process-wide in-memory store."""
    return InMemoryStore()


def get_project_service(
    store: Annotated[InMemoryStore, Depends(get_store)],
) -> ProjectService:
    """Build the project service from the current store."""
    return ProjectService(store.projects, store.tickets, store.subtasks)
