# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Base: shared environment and tooling
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# ---------------------------------------------------------------------------
# Development: dev dependencies + editable install (hot reload)
# ---------------------------------------------------------------------------
FROM base AS development

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

EXPOSE 8000
CMD ["uvicorn", "tickets_management.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# Production: no dev dependencies, non-editable install
# ---------------------------------------------------------------------------
FROM base AS production

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev --no-editable

EXPOSE 8000
CMD ["uvicorn", "tickets_management.main:app", "--host", "0.0.0.0", "--port", "8000"]
