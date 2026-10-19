"""Shared pytest configuration and fixtures."""

import os
from collections.abc import Iterator

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://user:password@localhost:5432/tickets_management",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest
from fastapi.testclient import TestClient

from tickets_management.api.deps import get_store
from tickets_management.main import app
from tickets_management.repositories.memory import InMemoryStore


@pytest.fixture
def store() -> InMemoryStore:
    """Return a fresh in-memory store for each test."""
    return InMemoryStore()


@pytest.fixture
def client(store: InMemoryStore) -> Iterator[TestClient]:
    """Return a client bound to the fresh store."""
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
