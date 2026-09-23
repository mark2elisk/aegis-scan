import hashlib
import logging

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Receive, Scope, Send

from app.ai.explain import explicar
from app.config import settings
from app.models import ResultadoEscaneo, Veredicto
from app.scanner import heuristics
from app.scanner.clamav import ClamAVNoDisponible, comprobar_disponibilidad, escanear_bytes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("aegisscan")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AegisScan",
    description="Escaneo de archivos con ClamAV + explicación de los resultados con IA.",
    version="0.3.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class LimiteTamanoMiddleware:
    """Rechaza la petición por Content-Length antes de que FastAPI parsee el
    cuerpo multipart completo.

    Sin esto, `UploadFile` no protege de nada: Starlette recibe y bufferiza
    (memoria y, si supera el umbral, disco) el archivo ENTERO como parte de
    resolver el parámetro `archivo: UploadFile = File(...)`, antes de que el
    endpoint llegue a comprobar `max_upload_mb`. Un archivo de varios GB se
    recibiría entero igualmente. Esta comprobación por cabecera es la primera
    línea de defensa (barata, antes de leer nada del cuerpo); no sustituye a
    un límite de tamaño en el proxy/servidor de producción, que sigue siendo
    necesario porque un cliente podría mentir sobre el Content-Length.
    """

    # Margen sobre el límite real para no rechazar peticiones legítimas cerca
    # del límite: multipart añade sus propias cabeceras y boundaries.
    MARGEN_MULTIPART_BYTES = 64 * 1024

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes + self.MARGEN_MULTIPART_BYTES

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            content_length = next(
                (v for k, v in scope.get("headers", []) if k == b"content-length"),
                None,
            )
            if content_length is not None:
                try:
                    declarado = int(content_length)
                except ValueError:
                    declarado = None
                if declarado is not None and declarado > self.max_bytes:
                    respuesta = JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"El archivo supera el límite de {settings.max_upload_mb} MB."
                        },
                    )
                    await respuesta(scope, receive, send)
                    return
        await self.app(scope, receive, send)


app.add_middleware(LimiteTamanoMiddleware, max_bytes=settings.max_upload_bytes)


@app.exception_handler(Exception)
async def error_no_controlado(request: Request, exc: Exception):
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ha ocurrido un error inesperado. Vuelve a intentarlo."},
    )


@app.get("/health")
def health():
    return {
        "estado": "ok",
        "clamav_disponible": comprobar_disponibilidad(),
        "ia_activa": settings.ai_provider != "none" and bool(settings.openai_api_key),
    }


@app.post("/scan", response_model=ResultadoEscaneo)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def escanear(request: Request, archivo: UploadFile = File(...)):
    # Lee hasta max_upload_bytes + 1: si se supera, se rechaza sin cargar el
    # archivo entero en memoria innecesariamente.
    limite = settings.max_upload_bytes
    datos = await archivo.read(limite + 1)
    if len(datos) > limite:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {settings.max_upload_mb} MB.",
        )
    if not datos:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    nombre = archivo.filename or "archivo_sin_nombre"
    sha256 = hashlib.sha256(datos).hexdigest()

    señales = heuristics.analizar(datos, nombre)

    # escanear_bytes() y explicar() son llamadas de red síncronas (clamd,
    # OpenAI). Ejecutarlas directamente en un endpoint async bloquearía el
    # bucle de eventos para el resto de peticiones concurrentes.
    try:
        veredicto, firma = await run_in_threadpool(escanear_bytes, datos)
    except ClamAVNoDisponible as exc:
        logger.error("ClamAV no disponible: %s", exc)
        veredicto, firma = Veredicto.ERROR, None

    if veredicto == Veredicto.LIMPIO and (señales.entropia_alta or señales.extension_sospechosa):
        # Sin firma conocida, pero hay señales heurísticas: no lo damos por limpio sin más.
        veredicto = Veredicto.SOSPECHOSO

    explicacion = await run_in_threadpool(explicar, veredicto, señales, firma)

    return ResultadoEscaneo(
        nombre_archivo=nombre,
        sha256=sha256,
        veredicto=veredicto,
        firma_clamav=firma,
        heuristicas=señales,
        explicacion_ia=explicacion,
    )
