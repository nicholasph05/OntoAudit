"""
Pruebas de la API. TestClient arranca la app completa (agentes incluidos).
"""
import json

import pytest
from fastapi.testclient import TestClient

from tests.test_analizador import sitio  # noqa: F401


@pytest.fixture(scope="module")
def cliente():
    import os
    os.environ["ONTOAUDIT_PERMITIR_RED_LOCAL"] = "1"   # para auditar el sitio local de prueba
    from api.main import app
    with TestClient(app) as c:
        yield c


def _leer_eventos(respuesta):
    eventos, tipo = [], None
    for linea in respuesta.iter_lines():
        if linea.startswith("event: "):
            tipo = linea[7:]
        elif linea.startswith("data: "):
            eventos.append((tipo, json.loads(linea[6:])))
    return eventos


def test_salud(cliente):
    r = cliente.get("/api/salud").json()
    assert r["estado"] == "ok" and len(r["agentes"]) == 3


def test_problemas_de_la_ontologia(cliente):
    assert len(cliente.get("/api/ontologia/problemas").json()) == 6


def test_auditoria_completa(cliente, sitio):  # noqa: F811
    r = cliente.post("/api/auditorias", json={"url": sitio + "/"})
    assert r.status_code == 202
    hilo = r.json()["auditoria"]

    with cliente.stream("GET", f"/api/auditorias/{hilo}/eventos") as flujo:
        eventos = _leer_eventos(flujo)
    acl = [e for t, e in eventos if t == "acl"]
    fin = [e for t, e in eventos if t == "fin"][0]
    assert [e["performativa"] for e in acl] == ["request", "request", "agree", "request", "inform", "inform"]
    assert fin["id"] == f"urn:ontoaudit:auditoria:{hilo}"

    informe = cliente.get(f"/api/auditorias/{hilo}")
    assert informe.headers["content-type"].startswith("application/ld+json")
    assert "@context" in informe.json()

    turtle = cliente.get(f"/api/auditorias/{hilo}", headers={"Accept": "text/turtle"})
    assert "earl:Assertion" in turtle.text

    assert any(a["@id"].endswith(hilo) for a in cliente.get("/api/auditorias").json())
    assert len(cliente.get("/api/sitios/historial", params={"url": sitio + "/"}).json()) >= 1


def test_rechaza_url_invalida(cliente):
    assert cliente.post("/api/auditorias", json={"url": "ftp://x"}).status_code == 400


def test_auditoria_inexistente(cliente):
    assert cliente.get("/api/auditorias/noexiste").status_code == 404