import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from agentes.analizador import (
    AnalisisNoPermitido, SitioNoDisponible, analizar, contar_errores_sintaxis, normalizar_url,
)

PAGINA = """<!DOCTYPE html>
<html lang="es"><head><title>Tienda</title>
<link rel="stylesheet" href="estilos.css"></head>
<body>
  <img src="foto.png"><img src="logo.png" alt="Logo"><img src="foto.png">
  <p><b>texto mal cerrado</p></div>
</body></html>"""


@pytest.fixture
def sitio(tmp_path):
    """Levanta un servidor web local con una página de prueba."""
    (tmp_path / "index.html").write_text(PAGINA, encoding="utf-8")
    (tmp_path / "foto.png").write_bytes(b"x" * 300_000)
    (tmp_path / "logo.png").write_bytes(b"x" * 1_000)
    (tmp_path / "estilos.css").write_text("body{}")
    (tmp_path / "privado").mkdir()
    (tmp_path / "privado" / "index.html").write_text(PAGINA)
    (tmp_path / "robots.txt").write_text("User-agent: *\nDisallow: /privado/\n")

    manejador = functools.partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    manejador.log_message = lambda *a: None  # silencioso
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_port}"
    servidor.shutdown()


def test_mide_las_metricas(sitio):
    m = analizar(sitio + "/")
    assert m["total_imagenes"] == 3
    assert m["imagenes_sin_alt"] == 2
    assert m["img_sin_alt_pct"] == pytest.approx(66.7)
    assert m["sin_titulo"] == 0
    assert m["sin_meta_descripcion"] == 1
    assert m["errores_sintaxis"] >= 1
    assert 0.28 <= m["peso_pagina_mb"] <= 0.31   # foto.png se cuenta una sola vez


def test_respeta_robots_txt(sitio):
    with pytest.raises(AnalisisNoPermitido):
        analizar(sitio + "/privado/")


def test_pagina_inexistente(sitio):
    with pytest.raises(SitioNoDisponible):
        analizar(sitio + "/no-existe.html")


def test_html_limpio_no_tiene_errores():
    assert contar_errores_sintaxis("<!DOCTYPE html><html><head><title>t</title></head><body><p>ok</p></body></html>") == 0


@pytest.mark.parametrize("entrada,esperada", [
    ("ejemplo.com", "https://ejemplo.com"),
    ("  http://a.co/x ", "http://a.co/x"),
])
def test_normaliza_url(entrada, esperada):
    assert normalizar_url(entrada) == esperada


def test_rechaza_url_invalida():
    with pytest.raises(ValueError):
        normalizar_url("ftp://archivo")