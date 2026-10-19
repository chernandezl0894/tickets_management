"""Smoke tests for the domain entities."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from tickets_management.domain.enum import (
    Channel,
    Platform,
    Priority,
    TicketType,
)
from tickets_management.domain.models import (
    OtpCode,
    Project,
    Reminder,
    Subtask,
    Ticket,
    User,
)


def test_ticket_defaults_to_medium_priority() -> None:
    """A new ticket is created with medium priority."""
    ticket = Ticket(
        project_id=uuid4(),
        type=TicketType.ISSUE,
        title="Smoke test ticket",
    )

    assert ticket.priority is Priority.MEDIUM
    assert ticket.priority.value == "medium"


def test_ticket_type_accepts_valid_values_and_rejects_unknown_values() -> None:
    """TicketType lookup accepts known values and rejects unknown ones."""
    assert TicketType("feature") is TicketType.FEATURE
    with pytest.raises(ValueError):
        TicketType("epic")


def test_every_entity_can_be_constructed() -> None:
    """Every domain entity can be instantiated and receives UTC timestamps."""
    now = datetime.now(UTC)

    user = User(name="Ada Lovelace", telegram_chat_id=123456)
    project = Project(
        name="Tickets",
        slug="tickets",
        platform=Platform.GITHUB,
        repo_url="https://github.com/example/tickets",
    )
    ticket = Ticket(
        project_id=project.id,
        type=TicketType.FEATURE,
        title="Smoke test ticket",
    )
    subtask = Subtask(ticket_id=ticket.id, title="Smoke test subtask")
    reminder = Reminder(
        ticket_id=ticket.id,
        user_id=user.id,
        remind_at=now,
        channel=Channel.TELEGRAM,
    )
    otp_code = OtpCode(
        telegram_chat_id=user.telegram_chat_id,
        code_hash="hashed-code",
        expires_at=now,
    )

    entities = (user, project, ticket, subtask, reminder, otp_code)
    for entity in entities:
        assert isinstance(entity.id, UUID)
        assert entity.created_at.tzinfo is UTC
        assert entity.updated_at.tzinfo is UTC
