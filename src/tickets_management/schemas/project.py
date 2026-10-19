"""Input and output schemas for projects."""

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field, HttpUrl

from tickets_management.domain.enum import Platform
from tickets_management.schemas.base import Schema

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class ProjectCreate(Schema):
    """Payload accepted when registering a project."""

    name: str
    slug: str = Field(pattern=SLUG_PATTERN)
    platform: Platform
    repo_url: HttpUrl
    description: str = ""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tickets Management",
                "slug": "tickets-management",
                "platform": "github",
                "repo_url": "https://github.com/example/tickets-management",
                "description": "Centralized ticket management service.",
            }
        }
    )


class ProjectUpdate(Schema):
    """Payload accepted when partially updating a project."""

    name: str | None = None
    slug: str | None = Field(default=None, pattern=SLUG_PATTERN)
    platform: Platform | None = None
    repo_url: HttpUrl | None = None
    description: str | None = None
    is_active: bool | None = None


class ProjectRead(Schema):
    """Project data exposed to API clients."""

    id: UUID
    name: str
    slug: str
    platform: Platform
    repo_url: HttpUrl
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
