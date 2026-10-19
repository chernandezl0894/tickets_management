"""Project API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from tickets_management.api.deps import PaginationDep, get_project_service
from tickets_management.core.openapi import problem_responses
from tickets_management.schemas.project import (
    ProjectCreate,
    ProjectList,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)
from tickets_management.services.projects import ProjectService

COMMON_RESPONSES = problem_responses(
    not_found="No se encontró el proyecto solicitado.",
    conflict="Ya existe un proyecto con el slug indicado.",
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses=COMMON_RESPONSES,
)


@router.get(
    "",
    response_model=ProjectList,
    summary="Listar proyectos",
    description=(
        "Devuelve una página de proyectos ordenados por fecha de creación. "
        "Usa `limit` y `offset` para navegar por los resultados. El total de "
        "proyectos se incluye en el cuerpo y en la cabecera `X-Total-Count`."
    ),
)
def list_projects(
    response: Response,
    pagination: PaginationDep,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectList:
    """Return one page of projects and the total number of projects."""
    projects, total = service.list(
        limit=pagination.limit,
        offset=pagination.offset,
    )
    response.headers["X-Total-Count"] = str(total)
    return ProjectList(
        items=[ProjectRead.model_validate(project) for project in projects],
        total=total,
    )


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto",
    description=(
        "Registra un proyecto nuevo. El `slug` debe ser único y cumplir el "
        "formato URL en minúsculas. Devuelve el proyecto creado con sus "
        "identificadores y fechas de auditoría."
    ),
)
def create_project(
    payload: ProjectCreate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Create a project, rejecting an already used slug."""
    return ProjectRead.model_validate(service.create(payload))


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Obtener proyecto",
    description=(
        "Devuelve un proyecto por su identificador. Responde `404` si el "
        "proyecto no existe."
    ),
)
def get_project(
    project_id: UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Return a project by id."""
    return ProjectRead.model_validate(service.get(project_id))


@router.get(
    "/{project_id}/summary",
    response_model=ProjectSummary,
    summary="Resumir tickets del proyecto",
    description=(
        "Devuelve el número total de tickets, los contadores agrupados por "
        "estado y prioridad, y la cantidad de subtareas pendientes de todos "
        "los tickets del proyecto. Responde `404` si el proyecto no existe."
    ),
)
def get_project_summary(
    project_id: UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectSummary:
    """Return ticket counters and pending subtasks for a project."""
    return service.summary(project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Actualizar proyecto",
    description=(
        "Actualiza parcialmente un proyecto. Solo se modifican los campos "
        "enviados. Si se cambia el `slug`, el nuevo valor debe seguir siendo "
        "único. Al desactivar un proyecto se conservan sus tickets existentes."
    ),
)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Partially update a project."""
    return ProjectRead.model_validate(service.update(project_id, payload))


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar proyecto",
    description=(
        "Elimina un proyecto junto con todos sus tickets y subtareas. La "
        "operación es irreversible y responde `204` sin cuerpo."
    ),
)
def delete_project(
    project_id: UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Delete a project and its tickets and subtasks."""
    service.delete(project_id)
