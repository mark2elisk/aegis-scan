from app.ai.explain import explicar
from app.models import Heuristicas, Veredicto

_HEURISTICAS_NEUTRAS = Heuristicas(
    entropia=3.0,
    entropia_alta=False,
    extension=".txt",
    tipo_mime_detectado="text/plain",
    extension_sospechosa=False,
    tamano_bytes=100,
)


def test_sin_cliente_de_ia_usa_explicacion_local_para_infectado():
    texto = explicar(Veredicto.INFECTADO, _HEURISTICAS_NEUTRAS, firma="Eicar-Test-Signature")
    assert "Eicar-Test-Signature" in texto
    assert "no lo abras" in texto.lower() or "elimínalo" in texto.lower()


def test_sin_cliente_de_ia_usa_explicacion_local_para_sospechoso_por_entropia():
    heuristicas = _HEURISTICAS_NEUTRAS.model_copy(update={"entropia_alta": True})
    texto = explicar(Veredicto.SOSPECHOSO, heuristicas, firma=None)
    assert "entropía" in texto.lower() or "comprimido" in texto.lower() or "cifrado" in texto.lower()


def test_sin_cliente_de_ia_usa_explicacion_local_para_limpio():
    texto = explicar(Veredicto.LIMPIO, _HEURISTICAS_NEUTRAS, firma=None)
    assert "no se ha detectado" in texto.lower()


def test_sin_cliente_de_ia_usa_explicacion_local_para_error():
    texto = explicar(Veredicto.ERROR, _HEURISTICAS_NEUTRAS, firma=None)
    assert "no se ha podido" in texto.lower()
