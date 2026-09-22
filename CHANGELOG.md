# Historial de versiones

Formato basado en versionado semántico (vMAYOR.MENOR.PARCHE).

## [v0.2.0] - 2026-09-22
### Cambiado
- El escaneo con ClamAV y la explicación con IA (ambas llamadas de red
  síncronas) ahora se ejecutan en un threadpool desde el endpoint async, en
  vez de bloquear el bucle de eventos durante cada petición.
- El cliente de OpenAI se crea una sola vez y se reutiliza, en vez de uno
  nuevo por petición.
- CORS ya no está abierto a cualquier origen (`*`): es configurable por
  variable de entorno (`CORS_ORIGINS`), con `http://localhost:3000` por
  defecto.
- El frontend ya arrastra y suelta archivos de verdad (antes solo hacía
  clic, pese a llamarse "zona de arrastrar"); se añadió un indicador de
  carga animado.

### Añadido
- Límite de peticiones a `/scan` por IP (`RATE_LIMIT_PER_MINUTE`, 10/min por defecto).
- Manejador global de errores no controlados.
- Tests automáticos (heurísticas y endpoints) y CI que los ejecuta en cada push/PR.
- Dependencia condicional por plataforma para `python-magic` (en Windows sin
  Docker, `python-magic` a secas no funciona sin `libmagic`; ahora se
  instala automáticamente `python-magic-bin` en su lugar).

## [v0.1.0] - 2026-09-22
### Añadido
- Primer MVP: backend FastAPI con escaneo real vía ClamAV (`clamd`),
  señales heurísticas propias (entropía, extensión vs. tipo MIME real) y
  explicación del resultado en lenguaje llano con IA (con modo sin IA de
  respaldo si no hay clave configurada).
- Frontend Next.js mínimo: subir un archivo y ver el veredicto explicado.
- `docker-compose.yml` para levantar ClamAV + backend + frontend juntos.
- Documentación de arquitectura y hoja de ruta hacia un SaaS real.
