"""Version 1 API router."""

from fastapi import APIRouter

from tickets_management.api.v1.endpoints import projects, subtasks, tickets

router = APIRouter(prefix="/v1")
router.include_router(projects.router)
router.include_router(tickets.router)
router.include_router(subtasks.router)
