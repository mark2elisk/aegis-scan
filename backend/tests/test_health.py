from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_health_responde_con_la_forma_esperada():
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert isinstance(cuerpo["clamav_disponible"], bool)
    assert isinstance(cuerpo["ia_activa"], bool)


def test_scan_sin_archivo_devuelve_422():
    respuesta = cliente.post("/scan")
    assert respuesta.status_code == 422


def test_scan_con_archivo_vacio_devuelve_400():
    respuesta = cliente.post(
        "/scan",
        files={"archivo": ("vacio.txt", b"", "text/plain")},
    )
    assert respuesta.status_code == 400
