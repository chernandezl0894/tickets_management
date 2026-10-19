"""Backwards-compatible repository error exports."""

from tickets_management.core.errors import (
    ConflictError,
    NotFoundError,
    RepositoryError,
)

__all__ = ["ConflictError", "NotFoundError", "RepositoryError"]
