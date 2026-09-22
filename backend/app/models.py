from enum import Enum

from pydantic import BaseModel


class Veredicto(str, Enum):
    LIMPIO = "limpio"
    SOSPECHOSO = "sospechoso"
    INFECTADO = "infectado"
    ERROR = "error"


class Heuristicas(BaseModel):
    entropia: float
    entropia_alta: bool
    extension: str
    tipo_mime_detectado: str
    extension_sospechosa: bool
    tamano_bytes: int


class ResultadoEscaneo(BaseModel):
    nombre_archivo: str
    sha256: str
    veredicto: Veredicto
    firma_clamav: str | None = None
    heuristicas: Heuristicas
    explicacion_ia: str | None = None
