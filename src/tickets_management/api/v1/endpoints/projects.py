"""Project API endpoints."""

from typing import Any

from fastapi import APIRouter, status

from tickets_management.domain.models import Project
from tickets_management.schemas.project import ProjectCreate, ProjectRead

COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
}

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses=COMMON_RESPONSES,
)


@router.get("", response_model=list[ProjectRead], summary="List projects")
def list_projects() -> list[ProjectRead]:
    """Return the projects registered in the system."""
    return []


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
)
def create_project(payload: ProjectCreate) -> ProjectRead:
    """Validate the payload and return the created project."""
    project = Project(
        name=payload.name,
        slug=payload.slug,
        platform=payload.platform,
        repo_url=str(payload.repo_url),
        description=payload.description,
    )
    return ProjectRead.model_validate(project)
