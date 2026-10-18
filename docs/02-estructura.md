# Estructura de carpetas

Estructura de esqueleto (layout `src`). Todavía no contiene lógica: solo
paquetes (`__init__.py`) y carpetas vacías que definen dónde vivirá cada pieza.

```text
.
├── src/
│   └── tickets_management/
│       ├── __init__.py
│       ├── main.py                 # crea la app FastAPI y registra los routers
│       ├── core/                   # configuración, logging y seguridad transversal
│       ├── api/
│       │   ├── deps.py             # dependencias compartidas de FastAPI
│       │   └── v1/
│       │       ├── router.py       # agrupa los endpoints de la v1
│       │       └── endpoints/      # projects.py, tickets.py, auth.py, reminders.py
│       ├── domain/                 # enums y modelos del negocio
│       ├── schemas/                # modelos Pydantic de entrada y salida
│       ├── services/               # reglas de negocio
│       ├── repositories/           # acceso a datos (protocol.py, memory.py → postgres.py)
│       └── workers/                # scheduler y tareas en background
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── alembic/
│   └── versions/                   # migraciones de base de datos (Fase 6)
├── docs/                           # notas de cada fase
├── .env.example
└── .python-version
```

## Responsabilidad de cada carpeta

**`src/tickets_management/`** es el paquete raíz de la aplicación. Contiene el
punto de entrada (`main.py`) y agrupa todos los subpaquetes internos; nada de
fuera del paquete debería importar directamente sus módulos internos.

**`src/tickets_management/core/`** reúne la configuración y las utilidades
transversales que no pertenecen a ninguna funcionalidad concreta: ajustes de la
app con `pydantic-settings`, configuración de logging estructurado y helpers de
seguridad (JWT, hash de OTP). Es la base que consume el resto de capas.

**`src/tickets_management/api/`** define la capa HTTP. Aquí viven las
dependencias compartidas de FastAPI (`deps.py`) y las versiones de la API; su
único trabajo es traducir peticiones HTTP a llamadas de servicio y respuestas,
sin lógica de negocio.

**`src/tickets_management/api/v1/`** agrupa la versión 1 de la API: el router
que une los distintos recursos y, en `endpoints/`, un módulo por recurso
(proyectos, tickets, autenticación y recordatorios).

**`src/tickets_management/domain/`** contiene los conceptos centrales del
negocio: enumeraciones y modelos/entidades independientes de frameworks, que
describen qué es un proyecto, un ticket, su prioridad o sus subtareas.

**`src/tickets_management/schemas/`** concentra los modelos Pydantic que
describen la forma de los datos en el borde de la API (payloads de entrada y de
salida), separando ese contrato de los modelos del dominio.

**`src/tickets_management/services/`** implementa las reglas de negocio y
orquesta los casos de uso: validaciones, priorización, recordatorios, etc.
Coordina repositorios y dominio sin conocer detalles de HTTP ni de la base de
datos.

**`src/tickets_management/repositories/`** es la capa de acceso a datos. Define
la interfaz (`protocol.py`) y una implementación en memoria para desarrollo
(`memory.py`), que más adelante se sustituirá o complementará con una de
PostgreSQL sin afectar a los servicios.

**`src/tickets_management/workers/`** aloja el trabajo asíncrono en segundo
plano: el scheduler de recordatorios y las tareas que se ejecutan fuera del
ciclo de petición/respuesta.

**`tests/`** separa las pruebas automáticas: `unit/` para pruebas rápidas y
aisladas de cada capa, e `integration/` para las que cruzan varios componentes
(API, base de datos, workers). `conftest.py` contendrá las fixtures compartidas.

**`alembic/`** guarda la configuración de migraciones de base de datos; en
`versions/` se irán acumulando los scripts de migración generados por fase.

**`docs/`** es la documentación del proyecto, con una nota por fase (alcance,
toolchain, estructura, etc.).

## Pendiente (fuera de este esqueleto)

Archivos de la toolchain que llegan más adelante: `pyproject.toml`,
`docker-compose.yml`, `Dockerfile` (Fase 8) y `Makefile`.
