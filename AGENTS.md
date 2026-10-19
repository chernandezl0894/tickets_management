# AGENTS.md

## Context
FastAPI ticket-management service (multi-platform, multi-project), built in
phases. Source of truth in `docs/`: `00-alcance.md` (scope), `01-toolchain.md`,
`02-estructura.md` (folder responsibilities). Docs are in **Spanish**. The
human-facing setup guide is `README.md`; do not duplicate it here.

**Language rule:** code, comments, and docstrings MUST be in **English**; docs
and prose stay in Spanish.

## Commands (always via `uv`, never bare `python`/`pytest`)
The package uses a `src/` layout and is only importable after `uv sync`.
- Run the API: `uv run uvicorn tickets_management.main:app --reload`
- Tests: `uv run pytest` · one test: `uv run pytest tests/unit/test_x.py::test_name`
- Lint/format: `uv run ruff check .` / `uv run ruff format .`
- Types: `uv run mypy .`
- Make shortcuts: `make` (help), `make check` (lint + typecheck + test).

## Docker
- Start stack (api + db + redis): `docker compose up -d`
- Status/health: `docker compose ps`
- Check Postgres: `docker compose exec db pg_isready -U user -d tickets_management`
- Check Redis: `docker compose exec redis redis-cli ping`
- Stop: `docker compose down` (`-v` also destroys volumes)
- Make shortcuts: `make up`, `make down`, `make logs`

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
- Drivers installed: `psycopg[binary]` (URL scheme `postgresql+psycopg`) and
  `redis`; no DB/Redis connection logic exists yet.
- Editor type checking: `[tool.pyright]` (strict, `extraPaths = ["src"]`) plus
  `src/tickets_management/py.typed`. Keep the `# pyright: ignore[reportCallIssue]`
  on `Settings()`; mypy does not need it.

## OpenCode
- `opencode.jsonc` sets the project default model
  (`opencode/deepseek-v4.1-flash-free`) and asks before `git push` via
  `permissions` (`shell` / `git push *` / `ask`). V2 uses `permissions`,
  `shell`, and `subagent` (not `permission`, `bash`, `task`).

## Commits
All commits MUST follow Conventional Commits and Semantic Release:
`<type>(<scope>): <description>` in imperative mood. Types: `feat`, `fix`,
`docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
Mark breaking changes with `!` or a `BREAKING CHANGE:` footer. `feat` bumps the
minor version, `fix` the patch, and a breaking change the major version.

## Gotchas
- `ruff` is configured in `pyproject.toml` and enforced by pre-commit
  (`.pre-commit-config.yaml`); run `uv run pre-commit install` after cloning.
  `mypy`/`pytest` still run on defaults. No CI yet.
- Docker: one multi-stage `Dockerfile` (`development`/`production` targets) plus
  `docker-compose.yml` (Postgres 16 + Redis 7). Alembic is still not wired up
  (`alembic/versions/` has no `alembic.ini`/`env.py`).
