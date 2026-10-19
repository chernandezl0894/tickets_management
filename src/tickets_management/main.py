"""Application entrypoint.

Creates the FastAPI instance and registers the API routes.
"""

from fastapi import FastAPI, Request

from tickets_management.api.v1.router import router as v1_router
from tickets_management.core.config import get_settings
from tickets_management.core.errors import register_exception_handlers

settings = get_settings()

app = FastAPI(
    title="Tickets Management API",
    version="0.0.1",
)

register_exception_handlers(app)
app.include_router(v1_router, prefix="/api")


@app.get("/", tags=["root"])
def root(request: Request) -> dict[str, str]:
    """Return the API name and a link to its interactive documentation."""
    return {
        "name": app.title,
        "docs_url": str(request.url_for("swagger_ui_html")),
    }


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Return service status and the current environment."""
    return {"status": "ok", "environment": settings.environment.value}
