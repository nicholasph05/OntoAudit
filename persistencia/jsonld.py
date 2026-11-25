"""
Etapa 6: convierte el diagnóstico en un informe Linked Data (JSON-LD).

Vocabularios usados:
  schema.org  -> Report, WebSite, PropertyValue (vocabulario general de la web)
  EARL (W3C)  -> Assertion, TestResult: estándar oficial para informes de evaluación
  oa          -> tu ontología (niveles, estados, problemas, recomendaciones)
"""
import json

from rdflib import Graph

OA = "https://nicholasph05.github.io/OntoAudit/ontologia#"

CONTEXTO = {
    "schema": "https://schema.org/",
    "earl": "http://www.w3.org/ns/earl#",
    "oa": OA,
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "schema:dateCreated": {"@type": "xsd:dateTime"},
    "schema:url": {"@type": "@id"},
    "oa:explicacionDifusa": {"@type": "@json"},
}

TODOS_LOS_PROBLEMAS = [
    "ProblemaCargaLenta", "ProblemaPaginaPesada", "ProblemaImagenesSinAlt",
    "ProblemaErroresSintaxis", "ProblemaSinTitulo", "ProblemaSinMetaDescripcion",
]


def a_jsonld(informe: dict) -> dict:
    """Diagnóstico del Agente Experto -> documento JSON-LD."""
    url = informe["url"]
    detectados = {p["problema"]: p for p in informe["problemas"]}
    id_auditoria = f"urn:ontoaudit:auditoria:{informe['auditoria']}"

    # Una aserción EARL por cada prueba: 'failed' si se detectó el problema, 'passed' si no
    aserciones = []
    for nombre in TODOS_LOS_PROBLEMAS:
        problema = detectados.get(nombre)
        aserciones.append({
            "@id": f"{id_auditoria}/{nombre}",
            "@type": "earl:Assertion",
            "earl:assertedBy": {"@id": "urn:ontoaudit:agente:experto"},
            "earl:subject": {"@id": url},
            "earl:test": {"@id": f"oa:{nombre}"},
            "earl:mode": {"@id": "earl:automatic"},
            "earl:result": {
                "@type": "earl:TestResult",
                "earl:outcome": {"@id": "earl:failed" if problema else "earl:passed"},
                **({"earl:info": problema["explicacion"]} if problema else {}),
            },
        })

    return {
        "@context": CONTEXTO,
        "@id": id_auditoria,
        "@type": ["schema:Report", "oa:Auditoria"],
        "schema:name": f"Auditoría de mantenimiento de {url}",
        "schema:dateCreated": informe["fecha"],
        "schema:author": {"@id": "urn:ontoaudit:agente:notificador"},
        # Valor con su tipo explícito (rango xsd:decimal en la ontología)
        "oa:puntajeDifuso": {"@value": str(informe["difuso"]["puntaje"]), "@type": "xsd:decimal"},
        "oa:analizaSitio": {
            "@id": url,
            "@type": ["schema:WebSite", "oa:SitioWeb"],
            "schema:url": url,
            "oa:tieneNivel": {"@id": f"oa:{informe['difuso']['nivel']}"},
            "oa:tieneEstado": {"@id": f"oa:{informe['estado']}"},
            "oa:presentaProblema": [{"@id": f"oa:{n}"} for n in detectados],
            "oa:necesitaRecomendacion": [
                {
                    "@id": f"oa:{p['recomendacion']}",
                    "oa:pasosSolucion": p["pasos"],
                    "oa:prioridad": p["prioridad"],
                }
                for p in sorted(detectados.values(), key=lambda p: p["prioridad"])
            ],
        },
        "schema:keywords": sorted({p["categoria"] for p in detectados.values()}),
        "schema:variableMeasured": [
            {"@type": "schema:PropertyValue", "schema:name": k, "schema:value": v}
            for k, v in informe["metricas"].items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        ],
        "schema:hasPart": aserciones,
        "oa:explicacionDifusa": {
            "riesgos": informe["difuso"]["riesgos"],
            "reglas": informe["difuso"]["reglas"],
        },
    }


def a_grafo(documento: dict) -> Graph:
    """JSON-LD -> grafo RDF (prueba de que el documento es Linked Data real)."""
    limpio = {k: v for k, v in documento.items() if k != "_id"}   # _id es de MongoDB
    return Graph().parse(data=json.dumps(limpio), format="json-ld")


def a_turtle(documento: dict) -> str:
    grafo = a_grafo(documento)
    grafo.bind("oa", OA)
    grafo.bind("earl", "http://www.w3.org/ns/earl#")
    grafo.bind("schema", "https://schema.org/")
    return grafo.serialize(format="turtle")