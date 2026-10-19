# Tickets Management

## ¿Qué es el proyecto?

Servicio para centralizar los tickets, requerimientos e issues de varios
proyectos y plataformas en un solo lugar, con priorización, subtareas y
recordatorios. Está construido con **FastAPI** y se desarrolla por fases.

> **Estado:** esqueleto en construcción. La configuración, el stack Docker y el
> tooling ya están listos; todavía no hay lógica de negocio ni conexión real a
> base de datos.

## Requisitos

| Herramienta | Versión / uso |
|---|---|
| Python | 3.14 (fijada en `.python-version`) |
| [uv](https://docs.astral.sh/uv/) | gestión de dependencias y entorno |
| Docker + Docker Compose | opcional, para PostgreSQL y Redis locales |
| `make` | opcional, atajos del `Makefile` |

## Instalación y uso

### Instalar dependencias

```bash
make install
```

Equivale a `uv sync` + `uv run pre-commit install` (hook de Ruff en cada commit).

### Configurar el entorno

```bash
cp .env.example .env
```

Edita `.env`. `DATABASE_URL` y `REDIS_URL` son obligatorias: si falta alguna, la
aplicación no arranca y el error indica la variable exacta. Las variables
`POSTGRES_*` deben coincidir con las credenciales de `DATABASE_URL`. Nunca
subas `.env` al repositorio.

### Arrancar la API

```bash
make run
```

Queda disponible en:

- Documentación: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>
- Raíz: <http://127.0.0.1:8000/>

### Comandos disponibles

Ejecuta `make` sin argumentos para ver la ayuda.

| Comando | Qué hace |
|---|---|
| `make install` | Sincroniza dependencias e instala el hook de pre-commit |
| `make run` | Arranca uvicorn con `--reload` |
| `make lint` | Revisa el código con Ruff |
| `make format` | Formatea el código con Ruff |
| `make typecheck` | Comprueba tipos con mypy en modo estricto |
| `make test` | Ejecuta los tests |
| `make test-cov` | Ejecuta los tests con cobertura |
| `make check` | `lint` + `typecheck` + `test` (lo que usará el CI) |
| `make up` | Levanta el stack de Docker Compose |
| `make down` | Detiene el stack (conserva los volúmenes) |
| `make logs` | Sigue los logs de Docker Compose |
| `make clean` | Borra `__pycache__`, `.pytest_cache`, `.ruff_cache` y `.mypy_cache` |

### Docker

```bash
make up                                                # api + PostgreSQL 16 + Redis 7
docker compose ps                                      # estado y salud
docker compose exec db pg_isready -U user -d tickets_management
docker compose exec redis redis-cli ping               # -> PONG
make logs
make down
```

`make down` conserva los datos; `docker compose down -v` borra también los
volúmenes (destructivo). Para construir la imagen de producción:

```bash
docker build --target production -t tickets-management:prod .
```

## Estructura de carpetas

```text
src/tickets_management/
├── main.py             # crea la app FastAPI y registra las rutas
├── core/               # configuración y utilidades transversales
├── api/                # capa HTTP (v1/endpoints/)
├── domain/             # modelos y enums del negocio
├── schemas/            # modelos Pydantic de entrada y salida
├── services/           # reglas de negocio
├── repositories/       # acceso a datos (protocol.py, memory.py)
└── workers/            # scheduler y tareas en background
tests/
├── unit/
└── integration/
docs/                   # alcance, toolchain y estructura
alembic/                # migraciones (pendiente de configurar)
```
