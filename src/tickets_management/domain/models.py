"""Framework-independent domain entities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from tickets_management.domain.enum import (
    Channel,
    Platform,
    Priority,
    ReminderStatus,
    TicketStatus,
    TicketType,
)


def _utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    """Return ``value`` normalized to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(kw_only=True)
class BaseEntity:
    """Common identity and audit fields for every entity."""

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        """Generate a missing identifier and normalize timestamps to UTC."""
        if self.id is None:
            self.id = uuid4()
        self.created_at = _as_utc(self.created_at)
        self.updated_at = _as_utc(self.updated_at)

    def touch(self) -> None:
        """Mark the entity as updated right now."""
        self.updated_at = _utc_now()


@dataclass(kw_only=True)
class Project(BaseEntity):
    """A repository or workspace tracked by the application."""

    name: str
    slug: str
    platform: Platform
    repo_url: str
    description: str = ""
    is_active: bool = True


@dataclass(kw_only=True)
class Ticket(BaseEntity):
    """A unit of work belonging to a project."""

    project_id: UUID
    type: TicketType
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    external_ref: str | None = None
    due_at: datetime | None = None


@dataclass(kw_only=True)
class Subtask(BaseEntity):
    """A checklist item that belongs to a ticket."""

    ticket_id: UUID
    title: str
    is_done: bool = False
    position: int = 0


@dataclass(kw_only=True)
class TicketHistory(BaseEntity):
    """An immutable record of a change made to a ticket field."""

    ticket_id: UUID
    field: str
    old: str | None
    new: str | None
    changed_at: datetime


@dataclass(kw_only=True)
class Reminder(BaseEntity):
    """A scheduled notification about a ticket."""

    ticket_id: UUID
    user_id: UUID
    remind_at: datetime
    channel: Channel
    message: str = ""
    status: ReminderStatus = ReminderStatus.SCHEDULED
    attempts: int = 0
    sent_at: datetime | None = None


@dataclass(kw_only=True)
class User(BaseEntity):
    """A person who receives notifications."""

    name: str
    telegram_chat_id: int
    is_active: bool = True


@dataclass(kw_only=True)
class OtpCode(BaseEntity):
    """A one-time password issued through Telegram."""

    telegram_chat_id: int
    code_hash: str
    expires_at: datetime
    consumed_at: datetime | None = None
    attempts: int = 0
