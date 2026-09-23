# Historial de versiones

Formato basado en versionado semántico (vMAYOR.MENOR.PARCHE).

## [v0.3.0] - 2026-09-23
### Seguridad
- Next.js actualizado de 14.2.35 a 16.3.6: `npm audit` reportaba 2
  vulnerabilidades (1 crítica, 1 alta) sin parche disponible dentro de la
  serie 14.x, incluyendo ejecución remota de código no autenticada en
  servidores Windows y en la API de optimización de imágenes con AVIF.
  React se mantiene en la 18.x (compatible con Next 16, sin necesidad de
  otro salto mayor). Requiere Node.js 20.9+ (la imagen Docker ya lo cumple).
- Dockerfile del frontend: build reproducible con `npm ci` a partir de un
  `package-lock.json` versionado, en vez de `npm install` sin lockfile.

### Añadido
- Middleware que rechaza subidas por `Content-Length` antes de que se
  parsee el cuerpo multipart: sin él, Starlette recibía y bufferizaba el
  archivo entero (memoria/disco) al resolver `UploadFile`, antes de que el
  endpoint llegara a comprobar `max_upload_mb` — un archivo de varios GB se
  habría recibido igualmente. Sigue recomendándose un límite también en el
  proxy de producción, porque un cliente podría declarar un `Content-Length`
  falso.
- Tests del flujo completo de `/scan`: veredictos limpio/infectado/sospechoso
  (por entropía), ClamAV no disponible, límite de tamaño real, rechazo
  temprano por `Content-Length` y límite de peticiones por minuto.
- Tests de las explicaciones locales de IA (`ai/explain.py`) para cada
  veredicto, sin necesitar clave de API.

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
