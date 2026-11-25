from rdflib.namespace import RDF

from ontologia.base_conocimiento import (
    OA, cargar_ontologia, clasificar_sitio, detectar_problemas, ontologia, problemas,
)


def test_la_ontologia_carga():
    grafo = cargar_ontologia(con_razonamiento=False)
    assert len(grafo) > 200


def test_el_razonador_deduce_la_inversa():
    # atiendeProblema nunca se escribió en Protégé: lo deduce el razonador
    assert (OA.RecOptimizarCarga, OA.atiendeProblema, OA.ProblemaCargaLenta) in ontologia()


def test_el_razonador_clasifica_problemas():
    assert (OA.ProblemaSinTitulo, RDF.type, OA.ProblemaSEO) in ontologia()
    assert (OA.ProblemaCargaLenta, RDF.type, OA.ProblemaRendimiento) in ontologia()


def test_hay_seis_problemas_con_solucion():
    lista = problemas()
    assert len(lista) == 6
    assert all(p["pasos"] and p["explicacion"] for p in lista)


def test_detecta_solo_lo_que_supera_el_umbral():
    encontrados = detectar_problemas({"tiempo_carga": 1.2, "img_sin_alt_pct": 40})
    assert [p["problema"] for p in encontrados] == ["ProblemaImagenesSinAlt"]


def test_sitio_urgente_es_critico():
    r = clasificar_sitio("https://x.com", "Urgente", ["ProblemaCargaLenta"])
    assert r["clase"] == "SitioCritico"
    assert r["estado"] == "Critico"
    assert r["recomendaciones"] == ["RecOptimizarCarga"]


def test_sitio_al_dia_es_excelente():
    r = clasificar_sitio("https://x.com", "AlDia", [])
    assert r["estado"] == "Excelente"
    assert r["recomendaciones"] == []