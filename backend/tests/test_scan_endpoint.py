from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Veredicto
from app.scanner.clamav import ClamAVNoDisponible

cliente = TestClient(app)


def _subir(nombre: str, contenido: bytes, tipo: str = "text/plain"):
    return cliente.post("/scan", files={"archivo": (nombre, contenido, tipo)})


def test_archivo_limpio_devuelve_veredicto_limpio():
    with patch("app.main.escanear_bytes", return_value=(Veredicto.LIMPIO, None)):
        respuesta = _subir("notas.txt", b"contenido normal de texto")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["veredicto"] == "limpio"
    assert cuerpo["firma_clamav"] is None
    assert cuerpo["explicacion_ia"]


def test_archivo_infectado_devuelve_veredicto_y_firma():
    with patch(
        "app.main.escanear_bytes",
        return_value=(Veredicto.INFECTADO, "Eicar-Test-Signature"),
    ):
        respuesta = _subir("eicar.txt", b"contenido de prueba")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["veredicto"] == "infectado"
    assert cuerpo["firma_clamav"] == "Eicar-Test-Signature"


def test_limpio_segun_clamav_pero_con_entropia_alta_sube_a_sospechoso():
    datos_aleatorios = bytes(range(256)) * 50  # entropía alta, sin firma conocida
    with patch("app.main.escanear_bytes", return_value=(Veredicto.LIMPIO, None)):
        respuesta = _subir("paquete.bin", datos_aleatorios, tipo="application/octet-stream")
    assert respuesta.status_code == 200
    assert respuesta.json()["veredicto"] == "sospechoso"


def test_clamav_no_disponible_devuelve_veredicto_error_sin_reventar():
    with patch("app.main.escanear_bytes", side_effect=ClamAVNoDisponible("sin conexión")):
        respuesta = _subir("notas.txt", b"contenido normal")
    assert respuesta.status_code == 200
    assert respuesta.json()["veredicto"] == "error"


def test_archivo_que_supera_el_limite_devuelve_413():
    with patch("app.main.escanear_bytes", return_value=(Veredicto.LIMPIO, None)):
        demasiado_grande = b"A" * (26 * 1024 * 1024)  # límite por defecto: 25 MB
        respuesta = _subir("grande.bin", demasiado_grande, tipo="application/octet-stream")
    assert respuesta.status_code == 413


def test_content_length_declarado_por_encima_del_limite_se_rechaza_sin_leer_el_cuerpo():
    # No se envía el archivo real: si el middleware no interceptase por
    # Content-Length, este test tendría que enviar 25+ MB de verdad para
    # comprobar el límite. Aquí comprobamos justo la primera línea de
    # defensa, antes de que se parsee nada del cuerpo multipart.
    with patch("app.main.escanear_bytes") as escanear_mock:
        respuesta = cliente.post(
            "/scan",
            content=b"cuerpo corto, no representativo",
            headers={
                "Content-Type": "multipart/form-data; boundary=x",
                "Content-Length": str(200 * 1024 * 1024),
            },
        )
    assert respuesta.status_code == 413
    escanear_mock.assert_not_called()


def test_mas_de_diez_peticiones_por_minuto_devuelve_429():
    # El limitador comparte estado (en memoria) con el resto de tests de este
    # módulo, todos bajo la misma IP simulada del TestClient: se reinicia
    # para que este test sea independiente del orden de ejecución.
    app.state.limiter.reset()
    with patch("app.main.escanear_bytes", return_value=(Veredicto.LIMPIO, None)):
        codigos = [
            _subir(f"archivo-{i}.txt", b"contenido").status_code for i in range(11)
        ]
    assert codigos[:10] == [200] * 10
    assert codigos[10] == 429
