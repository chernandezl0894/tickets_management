"""Tests for the in-memory repository layer."""

from uuid import uuid4

import pytest

from tickets_management.domain.enum import Platform, TicketType
from tickets_management.domain.models import Project, Subtask, Ticket
from tickets_management.repositories.errors import ConflictError, NotFoundError
from tickets_management.repositories.memory import InMemoryStore
from tickets_management.repositories.protocol import (
    ProjectRepository,
    SubtaskRepository,
    TicketRepository,
)


def _project() -> Project:
    """Build a valid project entity."""
    return Project(
        name="Tickets Management",
        slug="tickets-management",
        platform=Platform.GITHUB,
        repo_url="https://github.com/example/tickets-management",
    )


def test_project_round_trip_through_the_protocol() -> None:
    """A project can be inserted and retrieved through the protocol."""
    store = InMemoryStore()
    projects: ProjectRepository = store.projects
    project = _project()

    projects.add(project)

    assert projects.get(project.id) == project


def test_repositories_do_not_share_mutable_state() -> None:
    """Returned entities are copies, so callers cannot mutate stored data."""
    store = InMemoryStore()
    projects: ProjectRepository = store.projects
    projects.add(_project())

    listed = projects.list()
    listed[0].name = "mutated"
    assert projects.get(listed[0].id).name == "Tickets Management"

    retrieved = projects.get(listed[0].id)
    retrieved.description = "mutated"
    assert projects.get(retrieved.id).description == ""


def test_get_missing_id_raises_not_found() -> None:
    """Requesting an unknown id raises ``NotFoundError``."""
    store = InMemoryStore()
    projects: ProjectRepository = store.projects

    with pytest.raises(NotFoundError):
        projects.get(uuid4())


def test_add_duplicate_id_raises_conflict() -> None:
    """Storing an existing id raises ``ConflictError``."""
    store = InMemoryStore()
    projects: ProjectRepository = store.projects
    project = _project()

    projects.add(project)

    with pytest.raises(ConflictError):
        projects.add(project)


def test_update_and_delete_project() -> None:
    """Existing projects can be updated and deleted."""
    store = InMemoryStore()
    projects: ProjectRepository = store.projects
    project = projects.add(_project())

    project.name = "Renamed"
    projects.update(project)
    assert projects.get(project.id).name == "Renamed"

    projects.delete(project.id)
    with pytest.raises(NotFoundError):
        projects.get(project.id)


def test_ticket_and_subtask_repositories_are_available() -> None:
    """The store exposes the ticket and subtask repositories too."""
    store = InMemoryStore()
    tickets: TicketRepository = store.tickets
    subtasks: SubtaskRepository = store.subtasks
    project = store.projects.add(_project())

    ticket = tickets.add(
        Ticket(
            project_id=project.id,
            type=TicketType.FEATURE,
            title="Valid ticket title",
        )
    )
    subtask = subtasks.add(Subtask(ticket_id=ticket.id, title="Valid subtask title"))

    assert tickets.get(ticket.id).title == "Valid ticket title"
    assert subtasks.get(subtask.id).title == "Valid subtask title"


def test_ticket_search_checks_title_and_description_case_insensitively() -> None:
    """The repository search matches both text fields ignoring case."""
    store = InMemoryStore()
    project = store.projects.add(_project())
    title_match = store.tickets.add(
        Ticket(
            project_id=project.id,
            type=TicketType.FEATURE,
            title="Login flow",
            description="Add the authentication screen",
        )
    )
    description_match = store.tickets.add(
        Ticket(
            project_id=project.id,
            type=TicketType.FEATURE,
            title="Session timeout",
            description="Improve the LOGIN retry behaviour",
        )
    )
    store.tickets.add(
        Ticket(
            project_id=project.id,
            type=TicketType.FEATURE,
            title="Billing export",
            description="Download invoices as CSV",
        )
    )

    matches = store.tickets.search("LoGiN")

    assert {ticket.id for ticket in matches} == {
        title_match.id,
        description_match.id,
    }


def test_pending_subtask_count_is_scoped_to_the_ticket_ids() -> None:
    """The repository only counts unfinished subtasks for the given tickets."""
    store = InMemoryStore()
    project = store.projects.add(_project())
    first = store.tickets.add(
        Ticket(
            project_id=project.id,
            type=TicketType.FEATURE,
            title="First ticket",
        )
    )
    second = store.tickets.add(
        Ticket(
            project_id=project.id,
            type=TicketType.FEATURE,
            title="Second ticket",
        )
    )
    store.subtasks.add(Subtask(ticket_id=first.id, title="Pending", is_done=False))
    store.subtasks.add(Subtask(ticket_id=first.id, title="Done", is_done=True))
    store.subtasks.add(Subtask(ticket_id=second.id, title="Other pending"))

    assert store.subtasks.count_pending_by_ticket_ids({first.id}) == 1
    assert store.subtasks.count_pending_by_ticket_ids({first.id, second.id}) == 2
