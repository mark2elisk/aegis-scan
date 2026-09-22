"""Wrapper sobre clamd (el daemon de ClamAV) para escanear en memoria.

Habla con clamd por su protocolo de red — nunca se ejecuta el archivo ni se
invoca un shell con datos del usuario, así que no hay riesgo de inyección de
comandos por esta vía. clamd hace el análisis; aquí solo se interpreta su
respuesta.
"""
import io
import logging

import clamd

from app.config import settings
from app.models import Veredicto

logger = logging.getLogger(__name__)


class ClamAVNoDisponible(Exception):
    pass


def _cliente() -> clamd.ClamdNetworkSocket:
    return clamd.ClamdNetworkSocket(
        host=settings.clamd_host,
        port=settings.clamd_port,
        timeout=settings.clamd_timeout_seconds,
    )


def comprobar_disponibilidad() -> bool:
    try:
        return _cliente().ping() == "PONG"
    except Exception:  # noqa: BLE001 — cualquier fallo de red/daemon cuenta como "no disponible"
        return False


def escanear_bytes(datos: bytes) -> tuple[Veredicto, str | None]:
    """Escanea el contenido en memoria contra las firmas de ClamAV.

    Devuelve (veredicto, nombre_de_la_firma_si_la_hay).
    """
    try:
        cliente = _cliente()
        resultado = cliente.instream(io.BytesIO(datos))
    except clamd.ConnectionError as exc:
        raise ClamAVNoDisponible(
            f"No se pudo conectar con clamd en {settings.clamd_host}:{settings.clamd_port}"
        ) from exc

    estado, firma = resultado.get("stream", ("ERROR", None))

    if estado == "OK":
        return Veredicto.LIMPIO, None
    if estado == "FOUND":
        return Veredicto.INFECTADO, firma
    logger.warning("clamd devolvió un estado inesperado: %s", resultado)
    return Veredicto.ERROR, None
