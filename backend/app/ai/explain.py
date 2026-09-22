"""Explica el resultado del escaneo en lenguaje llano con un LLM.

Importante: a la IA solo le llegan METADATOS del escaneo (veredicto, firma,
señales heurísticas, nombre y tipo de archivo) — nunca el contenido del
archivo en sí. No hace falta, y evita mandar binarios potencialmente
maliciosos a un servicio de terceros.

Si no hay clave de API configurada, se devuelve una explicación por defecto
generada localmente (sin IA) para que el servicio siga funcionando igual.
"""
from app.config import settings
from app.models import Heuristicas, Veredicto

SYSTEM_PROMPT = """Eres el asistente de AegisScan, una plataforma de escaneo de archivos.
Recibes el resultado ya calculado de un escaneo (veredicto, firma de ClamAV si la hay,
y señales heurísticas). Tu trabajo es explicar ese resultado en español, en 2-4 frases,
en lenguaje llano para alguien sin conocimientos técnicos, y dar un siguiente paso
concreto (por ejemplo: "puedes descargarlo con confianza", "no lo abras y elimínalo",
"revísalo con otro antivirus antes de usarlo").

No inventes información que no esté en los datos que te doy. No prometas que un archivo
"limpio" es 100% seguro (ningún escáner lo garantiza): matiza que es la mejor información
disponible en el momento del análisis."""


def _explicacion_local(veredicto: Veredicto, heuristicas: Heuristicas, firma: str | None) -> str:
    """Explicación sin IA, para cuando no hay clave de API configurada."""
    if veredicto == Veredicto.INFECTADO:
        return (
            f"ClamAV ha identificado este archivo como amenaza conocida ({firma}). "
            "No lo abras ni lo ejecutes: elimínalo o ponlo en cuarentena."
        )
    if veredicto == Veredicto.SOSPECHOSO:
        motivos = []
        if heuristicas.entropia_alta:
            motivos.append("su contenido está muy comprimido o cifrado (entropía alta)")
        if heuristicas.extension_sospechosa:
            motivos.append("su extensión no coincide con su tipo de archivo real")
        motivo_txt = " y ".join(motivos) if motivos else "algunas señales heurísticas"
        return (
            f"No se ha encontrado una firma de virus conocida, pero {motivo_txt}. "
            "No es una detección confirmada — revísalo con precaución antes de abrirlo."
        )
    if veredicto == Veredicto.LIMPIO:
        return (
            "No se ha detectado ninguna firma de virus conocida ni señales heurísticas "
            "sospechosas. Es la mejor información disponible ahora mismo, pero ningún "
            "escáner puede garantizar el 100% frente a amenazas nuevas."
        )
    return "No se ha podido completar el análisis. Vuelve a intentarlo en unos minutos."


def _prompt_usuario(veredicto: Veredicto, heuristicas: Heuristicas, firma: str | None) -> str:
    return (
        f"Veredicto: {veredicto.value}\n"
        f"Firma de ClamAV: {firma or '(ninguna)'}\n"
        f"Entropía: {heuristicas.entropia} (alta: {heuristicas.entropia_alta})\n"
        f"Extensión: {heuristicas.extension}\n"
        f"Tipo MIME detectado: {heuristicas.tipo_mime_detectado}\n"
        f"Extensión sospechosa respecto al tipo real: {heuristicas.extension_sospechosa}"
    )


def explicar(veredicto: Veredicto, heuristicas: Heuristicas, firma: str | None = None) -> str:
    if settings.ai_provider == "none" or not settings.openai_api_key:
        return _explicacion_local(veredicto, heuristicas, firma)

    try:
        from openai import OpenAI

        cliente = OpenAI(api_key=settings.openai_api_key)
        respuesta = cliente.chat.completions.create(
            model=settings.openai_model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _prompt_usuario(veredicto, heuristicas, firma)},
            ],
        )
        texto = respuesta.choices[0].message.content
        return texto.strip() if texto else _explicacion_local(veredicto, heuristicas, firma)
    except Exception:  # noqa: BLE001 — si la IA falla, no debe tumbar el escaneo
        return _explicacion_local(veredicto, heuristicas, firma)
