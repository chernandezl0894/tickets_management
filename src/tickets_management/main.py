"""Application entrypoint.

Creates the FastAPI instance and registers the API routes.
"""

from fastapi import Request

from tickets_management.api.v1.router import router as v1_router
from tickets_management.core.config import get_settings
from tickets_management.core.errors import register_exception_handlers
from tickets_management.core.openapi import (
    API_DESCRIPTION,
    API_SUMMARY,
    OPENAPI_TAGS,
    DocumentedFastAPI,
)

settings = get_settings()

app = DocumentedFastAPI(
    title="Tickets Management API",
    summary=API_SUMMARY,
    description=API_DESCRIPTION,
    version="0.0.1",
    contact={
        "name": "Cristhian Hernandez",
        "url": "https://github.com/chernandezl0894/tickets_management",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=OPENAPI_TAGS,
)

register_exception_handlers(app)
app.include_router(v1_router, prefix="/api")


@app.get(
    "/",
    tags=["root"],
    summary="Información de la API",
    description="Devuelve el nombre de la API y el enlace a Swagger UI.",
)
def root(request: Request) -> dict[str, str]:
    """Return the API name and a link to its interactive documentation."""
    return {
        "name": app.title,
        "docs_url": str(request.url_for("swagger_ui_html")),
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Consultar estado del servicio",
    description="Devuelve el estado operativo y el entorno actual.",
)
def health() -> dict[str, str]:
    """Return service status and the current environment."""
    return {"status": "ok", "environment": settings.environment.value}
