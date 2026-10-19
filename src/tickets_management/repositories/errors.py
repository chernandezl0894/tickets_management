"""Repository exceptions."""


class RepositoryError(Exception):
    """Base class for repository-level errors."""


class NotFoundError(RepositoryError):
    """Raised when the requested entity does not exist."""


class ConflictError(RepositoryError):
    """Raised when an entity cannot be stored because it already exists."""
