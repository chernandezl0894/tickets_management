# AGENTS.md

## Context
FastAPI ticket-management service (multi-platform, multi-project), built in
phases. Source of truth in `docs/`: `00-alcance.md` (scope), `01-toolchain.md`,
`02-estructura.md` (folder responsibilities). Docs are in **Spanish**.

**Language rule:** code, comments, and docstrings MUST be in **English**; docs
and prose stay in Spanish.

## Commands (always via `uv`, never bare `python`/`pytest`)
The package uses a `src/` layout and is only importable after `uv sync`.
- Run the API: `uv run uvicorn tickets_management.main:app --reload`
- Tests: `uv run pytest` · one test: `uv run pytest tests/unit/test_x.py::test_name`
- Lint/format: `uv run ruff check .` / `uv run ruff format .`
- Types: `uv run mypy .`

## Layout
- Import name is `tickets_management` (underscore); distribution name is
  `tickets-management` (hyphen).
- Layers: `api/` (`v1/endpoints/`) → `services/` (business rules) →
  `repositories/` (`protocol.py` interface, `memory.py`) → `domain/`.
  `schemas/` = Pydantic input/output, `core/` = config, `workers/` = background.
- Still mostly a skeleton: most modules are empty `__init__.py` (e.g. `domain/`,
  `services/`, `repositories/`). Do not assume implementations exist.

## Config
- `core/config.py`: `Settings` + cached `get_settings()`. Required env vars:
  `DATABASE_URL`, `REDIS_URL`. The Pydantic mypy plugin is enabled, so
  `Settings()` type-checks without a `# type: ignore`.

## Gotchas
- `ruff` is configured in `pyproject.toml` and enforced by pre-commit
  (`.pre-commit-config.yaml`); run `uv run pre-commit install` after cloning.
  `mypy`/`pytest` still run on defaults. No CI yet.
- `Dockerfile` is empty and alembic is not wired up (`alembic/versions/` has no
  `alembic.ini`/`env.py`).
