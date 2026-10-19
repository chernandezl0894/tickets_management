"""Shared pytest configuration."""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://user:password@localhost:5432/tickets_management",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
