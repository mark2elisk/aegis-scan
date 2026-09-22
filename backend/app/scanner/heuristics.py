"""Señales heurísticas complementarias al motor de firmas (ClamAV).

No sustituyen a un antivirus real: son indicios adicionales (entropía alta,
extensión que no coincide con el tipo real del archivo) que ayudan a la capa
de IA a explicar mejor el resultado, y a detectar casos sospechosos que un
escáner de firmas por sí solo podría pasar por alto (por ejemplo, contenido
empaquetado/ofuscado).
"""
import math
import os
from collections import Counter

import magic

from app.models import Heuristicas

# Extensiones que casi nunca deberían venir con un tipo MIME de texto/imagen.
EXTENSIONES_EJECUTABLES = {
    ".exe", ".dll", ".scr", ".bat", ".cmd", ".com", ".msi",
    ".jar", ".apk", ".sh", ".ps1", ".vbs", ".js",
}

UMBRAL_ENTROPIA_ALTA = 7.5  # sobre un máximo teórico de 8.0 (byte aleatorio)


def calcular_entropia(datos: bytes) -> float:
    if not datos:
        return 0.0
    conteo = Counter(datos)
    total = len(datos)
    return -sum(
        (n / total) * math.log2(n / total)
        for n in conteo.values()
    )


def analizar(datos: bytes, nombre_archivo: str) -> Heuristicas:
    entropia = calcular_entropia(datos)
    extension = os.path.splitext(nombre_archivo)[1].lower()
    tipo_mime = magic.from_buffer(datos, mime=True)

    extension_sospechosa = (
        extension in EXTENSIONES_EJECUTABLES
        and not tipo_mime.startswith(("application/x-executable", "application/x-dosexec",
                                       "application/x-mach-binary", "application/java-archive",
                                       "application/vnd.android.package-archive",
                                       "application/x-sh", "text/x-shellscript"))
    )

    return Heuristicas(
        entropia=round(entropia, 3),
        entropia_alta=entropia >= UMBRAL_ENTROPIA_ALTA,
        extension=extension or "(sin extensión)",
        tipo_mime_detectado=tipo_mime,
        extension_sospechosa=extension_sospechosa,
        tamano_bytes=len(datos),
    )
