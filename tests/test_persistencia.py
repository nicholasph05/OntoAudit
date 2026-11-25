import copy

import mongomock
import pytest
from rdflib import Namespace, URIRef
from rdflib.namespace import RDF

from agentes.agente_experto import diagnosticar
from persistencia.jsonld import a_grafo, a_jsonld
from persistencia.repositorio import Repositorio
from persistencia.validacion import InformeInvalido, validar

OA = Namespace("https://nicholasph05.github.io/OntoAudit/ontologia#")
EARL = Namespace("http://www.w3.org/ns/earl#")

METRICAS = dict(tiempo_carga=4.0, peso_pagina_mb=1.0, img_sin_alt_pct=20, errores_sintaxis=3,
                sin_titulo=0, sin_meta_descripcion=1, total_imagenes=5, imagenes_sin_alt=1)


@pytest.fixture(scope="module")
def informe():
    return {**diagnosticar("https://ejemplo.com", METRICAS),
            "auditoria": "prueba1", "fecha": "2026-11-25T19:00:00+00:00"}


def test_el_documento_tiene_contexto_jsonld(informe):
    doc = a_jsonld(informe)
    assert "@context" in doc and doc["@type"] == ["schema:Report", "oa:Auditoria"]


def test_el_jsonld_es_rdf_valido(informe):
    grafo = a_grafo(a_jsonld(informe))
    sitio = URIRef("https://ejemplo.com")
    assert (sitio, RDF.type, OA.SitioWeb) in grafo
    assert (sitio, OA.presentaProblema, OA.ProblemaCargaLenta) in grafo


def test_hay_una_asercion_earl_por_prueba(informe):
    grafo = a_grafo(a_jsonld(informe))
    resultados = list(grafo.objects(None, EARL.outcome))
    assert len(resultados) == 6
    assert resultados.count(EARL.failed) == len(informe["problemas"])


def test_shacl_acepta_un_informe_correcto(informe):
    validar(a_jsonld(informe))   # no lanza excepción


def test_shacl_rechaza_un_nivel_inventado(informe):
    doc = copy.deepcopy(a_jsonld(informe))
    doc["oa:analizaSitio"]["oa:tieneNivel"] = {"@id": "oa:Regular"}
    with pytest.raises(InformeInvalido):
        validar(doc)


def test_shacl_rechaza_puntaje_fuera_de_rango(informe):
    doc = copy.deepcopy(a_jsonld(informe))
    doc["oa:puntajeDifuso"]["@value"] = "150"
    with pytest.raises(InformeInvalido):
        validar(doc)


def test_repositorio_guarda_y_consulta(informe):
    repo = Repositorio(mongomock.MongoClient())   # MongoDB simulado en memoria
    id_guardado = repo.guardar_informe(informe)
    assert id_guardado == "urn:ontoaudit:auditoria:prueba1"

    guardado = repo.obtener(id_guardado)
    assert guardado["@context"]["oa"].startswith("https://nicholasph05")
    assert len(a_grafo(guardado)) > 50          # sigue siendo Linked Data al leerlo
    assert len(repo.recientes()) == 1
    assert len(repo.historial("https://ejemplo.com")) == 1