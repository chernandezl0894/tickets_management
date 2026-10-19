# Fase 01 — CRUD ampliado, búsqueda, historial y cierre

## Objetivo

Cerrar la primera fase funcional del CRUD comprobando que el protocolo de
repositorios soporta nuevas consultas sin filtrar lógica en los routers:

- Búsqueda de tickets por texto con `?q=`.
- Historial cronológico de cambios de un ticket.
- Resumen de tickets y subtareas por proyecto.

## Qué se construyó

### Búsqueda de tickets

`GET /api/v1/tickets?q=login` busca sin distinguir mayúsculas en el título y la
descripción. La consulta se puede combinar con el resto de filtros (`project_id`,
`type`, `priority`, `status`) y mantiene el orden por prioridad y fecha límite.

La búsqueda vive en `TicketRepository.search()` y en
`InMemoryTicketRepository`, no en el endpoint. El servicio solo compone el
resultado con los demás filtros.

### Historial de cambios

`GET /api/v1/tickets/{ticket_id}/history` devuelve entradas con:

- `field`
- `old`
- `new`
- `changed_at`

Cada `PATCH` registra una entrada por cada campo que realmente cambia. Los
valores se serializan como texto; los enums usan su valor y las fechas usan ISO
8601. Se cubren, entre otros, los cambios de `status`, `priority` y `due_at`.

El historial se guarda en un repositorio propio (`TicketHistoryRepository`) y se
elimina en cascada al borrar un ticket o un proyecto.

### Resumen por proyecto

`GET /api/v1/projects/{project_id}/summary` devuelve:

```json
{
  "total": 3,
  "by_status": {
    "open": 1,
    "in_progress": 1,
    "blocked": 0,
    "done": 1,
    "closed": 0
  },
  "by_priority": {
    "high": 2,
    "medium": 1,
    "low": 0
  },
  "pending_subtasks": 2
}
```

Los contadores se calculan a partir de consultas del repositorio
(`list_by_project` y `count_pending_by_ticket_ids`) y de las reglas del servicio
de proyectos.

## Lo que aprendí

- **El protocolo es el punto de extensión correcto.** Añadir `search`,
  `list_by_project` y `count_pending_by_ticket_ids` mantuvo los routers
  declarativos y permitió probar la lógica sin pasar por HTTP.
- **Una entidad de historial es más simple que reconstruir cambios.** Guardar
  `field`, `old`, `new` y `changed_at` desacopla la auditoría del modelo actual
  del ticket y evita perder información cuando un valor cambia varias veces.
- **Serializar valores para auditoría requiere una decisión explícita.** Enums y
  fechas no se guardan como objetos: se convierten a texto estable para que el
  historial sea legible y fácil de consumir.
- **Los contadores deben tener un contrato estable.** Devolver todos los estados
  y prioridades, incluso con cero, simplifica el consumo desde el frontend.
- **La documentación OpenAPI también es código de contrato.** Los nuevos
  endpoints heredan las respuestas RFC 9457 y el esquema se regenera con
  `make openapi`; el test de contrato detecta si el JSON queda desactualizado.

## Lo que me costó

- **Nombrar métodos dentro de una clase que ya define `list`.** El método
  `TicketService.list` sombrea el builtin `list` en el cuerpo de la clase; una
  anotación `list[TicketHistory]` se interpretó como el método. Se resolvió con
  un alias de tipo a nivel de módulo.
- **Mantener el historial coherente con las transiciones de estado.** El
  registro debe ocurrir solo después de validar la regla de subtareas pendientes;
  de lo contrario un `409` podría dejar historia de un cambio que nunca se
  aplicó.
- **Cascadas invisibles.** Borrar un proyecto debe limpiar tickets, subtareas e
  historial. Es fácil olvidar el historial porque no se consulta desde el
  endpoint de proyectos.
- **Compatibilidad del contrato.** Añadir métodos al protocolo y nuevas
  dependencias a los servicios obliga a actualizar `deps.py` y el esquema
  exportado sin romper los endpoints existentes.

## Limitaciones y siguientes pasos

- El historial todavía **no registra al actor** (`changed_by`). Hace falta el
  sistema de autenticación/usuarios para saber quién hizo el cambio.
- El historial no está paginado; para tickets con muchas modificaciones habrá
  que añadir `limit`/`offset` o cursor.
- La persistencia sigue siendo en memoria. La siguiente fase debe mover estas
  consultas a SQLAlchemy sin cambiar los routers.
- El resumen se calcula en memoria; con base de datos conviene resolverlo con
  agregaciones SQL.
- Los recordatorios siguen siendo un placeholder de la fase de notificaciones.

## Verificación

```bash
make check
```

Incluye lint, typecheck estricto y la suite completa. También se regenera el
contrato con:

```bash
make openapi
```
