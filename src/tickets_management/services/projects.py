"""Project use cases."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from tickets_management.core.errors import ConflictError
from tickets_management.domain.models import Project
from tickets_management.repositories.protocol import (
    ProjectRepository,
    SubtaskRepository,
    TicketRepository,
)
from tickets_management.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Business rules for project management."""

    def __init__(
        self,
        projects: ProjectRepository,
        tickets: TicketRepository,
        subtasks: SubtaskRepository,
    ) -> None:
        self._projects = projects
        self._tickets = tickets
        self._subtasks = subtasks

    def list(self, *, limit: int, offset: int) -> tuple[list[Project], int]:
        """Return one page of projects and the total number of projects."""
        projects = self._projects.list()
        return projects[offset : offset + limit], len(projects)

    def get(self, project_id: UUID) -> Project:
        """Return a project or raise ``NotFoundError``."""
        return self._projects.get(project_id)

    def create(self, payload: ProjectCreate) -> Project:
        """Create a project if its slug is still available."""
        self._ensure_slug_available(payload.slug)
        project = Project(
            name=payload.name,
            slug=payload.slug,
            platform=payload.platform,
            repo_url=str(payload.repo_url),
            description=payload.description,
        )
        return self._projects.add(project)

    def update(self, project_id: UUID, payload: ProjectUpdate) -> Project:
        """Apply a partial update without touching ``updated_at`` when empty."""
        project = self._projects.get(project_id)
        changes = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not changes:
            return project

        new_slug = changes.get("slug")
        if isinstance(new_slug, str):
            self._ensure_slug_available(new_slug, exclude_id=project_id)

        if "repo_url" in changes:
            changes["repo_url"] = str(changes["repo_url"])

        changes["updated_at"] = datetime.now(UTC)
        return self._projects.update(replace(project, **changes))

    def delete(self, project_id: UUID) -> None:
        """Delete a project together with its tickets and their subtasks."""
        self._projects.get(project_id)

        ticket_ids = {
            ticket.id
            for ticket in self._tickets.list()
            if ticket.project_id == project_id
        }
        for subtask in self._subtasks.list():
            if subtask.ticket_id in ticket_ids:
                self._subtasks.delete(subtask.id)
        for ticket_id in ticket_ids:
            self._tickets.delete(ticket_id)

        self._projects.delete(project_id)

    def _ensure_slug_available(
        self, slug: str, *, exclude_id: UUID | None = None
    ) -> None:
        """Raise ``ConflictError`` when another project already uses the slug."""
        for project in self._projects.list():
            if project.slug == slug and project.id != exclude_id:
                raise ConflictError(f"Project with slug '{slug}' already exists")
