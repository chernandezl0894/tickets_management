# Tickets Management

## What is the project?

A service to centralize tickets, requirements, and issues from multiple projects
and platforms in a single place, with prioritization, subtasks, and reminders.
It is built with **FastAPI** and developed in phases.

> **Status:** API in active development. Projects, tickets, and subtasks are
> available; persistence is still in memory, and authentication and reminders
> are pending.

## Requirements

| Tool | Version / purpose |
|---|---|
| Python | 3.14 (pinned in `.python-version`) |
| [uv](https://docs.astral.sh/uv/) | dependency and environment management |
| Docker + Docker Compose | optional, for local PostgreSQL and Redis |
| `make` | optional, `Makefile` shortcuts |

## Installation and usage

### Install dependencies

```bash
make install
```

Equivalent to `uv sync` + `uv run pre-commit install` (Ruff hook on every
commit).

### Configure the environment

```bash
cp .env.example .env
```

Edit `.env`. `DATABASE_URL` and `REDIS_URL` are required: if either is missing,
the application will not start and the error names the exact variable. The
`POSTGRES_*` variables must match the credentials in `DATABASE_URL`. Never
commit `.env` to the repository.

### Run the API

```bash
make run
```

Available at:

- Docs: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>
- Exported schema: `docs/openapi.json` (regenerate with `make openapi`)
- Health check: <http://127.0.0.1:8000/health>
- Root: <http://127.0.0.1:8000/>

### Available commands

Run `make` with no arguments to see the help.

| Command | What it does |
|---|---|
| `make install` | Sync dependencies and install the pre-commit hook |
| `make run` | Start uvicorn with `--reload` |
| `make lint` | Lint the code with Ruff |
| `make format` | Format the code with Ruff |
| `make typecheck` | Type-check with mypy in strict mode |
| `make test` | Run the tests |
| `make test-cov` | Run the tests with coverage |
| `make check` | `lint` + `typecheck` + `test` (what CI will run) |
| `make openapi` | Export the OpenAPI schema to `docs/openapi.json` |
| `make up` | Start the Docker Compose stack |
| `make down` | Stop the stack (keeps volumes) |
| `make logs` | Follow Docker Compose logs |
| `make clean` | Remove `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache` |

### Docker

```bash
make up                                                # api + PostgreSQL 16 + Redis 7
docker compose ps                                      # status and health
docker compose exec db pg_isready -U user -d tickets_management
docker compose exec redis redis-cli ping               # -> PONG
make logs
make down
```

`make down` keeps the data; `docker compose down -v` also deletes the volumes
(destructive). To build the production image:

```bash
docker build --target production -t tickets-management:prod .
```

## Folder structure

```text
src/tickets_management/
├── main.py             # creates the FastAPI app and registers the routes
├── core/               # configuration and cross-cutting utilities
├── api/                # HTTP layer (v1/endpoints/)
├── domain/             # business models and enums
├── schemas/            # Pydantic input/output models
├── services/           # business rules
├── repositories/       # data access (protocol.py, memory.py)
└── workers/            # scheduler and background tasks
tests/
├── unit/
└── integration/
scripts/                # developer utilities (OpenAPI export)
docs/                   # scope, toolchain, structure, and openapi.json
alembic/                # migrations (not configured yet)
```
