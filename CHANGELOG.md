# Historial de versiones

Formato basado en versionado semántico (vMAYOR.MENOR.PARCHE).

## [v0.1.0] - 2026-09-22
### Añadido
- Primer MVP: backend FastAPI con escaneo real vía ClamAV (`clamd`),
  señales heurísticas propias (entropía, extensión vs. tipo MIME real) y
  explicación del resultado en lenguaje llano con IA (con modo sin IA de
  respaldo si no hay clave configurada).
- Frontend Next.js mínimo: subir un archivo y ver el veredicto explicado.
- `docker-compose.yml` para levantar ClamAV + backend + frontend juntos.
- Documentación de arquitectura y hoja de ruta hacia un SaaS real.
