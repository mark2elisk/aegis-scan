from app.scanner.heuristics import analizar, calcular_entropia


def test_entropia_de_datos_vacios_es_cero():
    assert calcular_entropia(b"") == 0.0


def test_entropia_de_bytes_repetidos_es_baja():
    # Un único byte repetido no aporta ninguna información: entropía 0.
    assert calcular_entropia(b"A" * 500) == 0.0


def test_entropia_de_datos_aleatorios_es_alta():
    datos = bytes(range(256)) * 20  # 256 valores distintos, bien repartidos
    assert calcular_entropia(datos) > 7.9


def test_extension_ejecutable_con_tipo_mime_de_texto_es_sospechosa():
    # Un .exe cuyo contenido real es texto plano: la extensión miente.
    contenido = b"esto es texto plano, no un ejecutable real" * 10
    resultado = analizar(contenido, "factura.exe")
    assert resultado.extension == ".exe"
    assert resultado.extension_sospechosa is True


def test_extension_de_texto_normal_no_es_sospechosa():
    resultado = analizar(b"hola mundo", "notas.txt")
    assert resultado.extension_sospechosa is False
