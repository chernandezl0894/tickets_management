"""Application entrypoint.

Creates the FastAPI instance and registers the API routes.
"""

from fastapi import FastAPI, Request

from tickets_management.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Tickets Management API",
    version="0.0.1",
)


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
