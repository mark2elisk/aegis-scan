import hashlib
import logging

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.concurrency import run_in_threadpool

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
    version="0.2.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


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
