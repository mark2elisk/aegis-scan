import hashlib
import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.ai.explain import explicar
from app.config import settings
from app.models import ResultadoEscaneo, Veredicto
from app.scanner import heuristics
from app.scanner.clamav import ClamAVNoDisponible, comprobar_disponibilidad, escanear_bytes

logger = logging.getLogger("aegisscan")

app = FastAPI(
    title="AegisScan",
    description="Escaneo de archivos con ClamAV + explicación de los resultados con IA.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar a los orígenes reales antes de producción
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "estado": "ok",
        "clamav_disponible": comprobar_disponibilidad(),
        "ia_activa": settings.ai_provider != "none" and bool(settings.openai_api_key),
    }


@app.post("/scan", response_model=ResultadoEscaneo)
async def escanear(archivo: UploadFile = File(...)):
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

    try:
        veredicto, firma = escanear_bytes(datos)
    except ClamAVNoDisponible as exc:
        logger.error("ClamAV no disponible: %s", exc)
        veredicto, firma = Veredicto.ERROR, None

    if veredicto == Veredicto.LIMPIO and (señales.entropia_alta or señales.extension_sospechosa):
        # Sin firma conocida, pero hay señales heurísticas: no lo damos por limpio sin más.
        veredicto = Veredicto.SOSPECHOSO

    explicacion = explicar(veredicto, señales, firma)

    return ResultadoEscaneo(
        nombre_archivo=nombre,
        sha256=sha256,
        veredicto=veredicto,
        firma_clamav=firma,
        heuristicas=señales,
        explicacion_ia=explicacion,
    )
