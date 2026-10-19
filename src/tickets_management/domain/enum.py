"""Domain enumerations shared by the business entities."""

from enum import StrEnum


class Platform(StrEnum):
    """Supported source-control platforms."""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"
    OTHER = "other"


class TicketType(StrEnum):
    """Kind of work tracked by a ticket."""

    CASE = "case"
    FEATURE = "feature"
    REQUEST = "request"
    ISSUE = "issue"


class Priority(StrEnum):
    """Ticket urgency levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TicketStatus(StrEnum):
    """Lifecycle states of a ticket."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CLOSED = "closed"


class Channel(StrEnum):
    """Notification channels available for reminders."""

    TELEGRAM = "telegram"


class ReminderStatus(StrEnum):
    """Delivery states of a reminder."""

    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
