"""
Etapa 2: la ontología desde Python.

Carga mantenimiento_web.owl, ejecuta el razonador OWL-RL (owlrl) y ofrece
consultas SPARQL que usarán los agentes.
"""
from functools import lru_cache
from pathlib import Path

import owlrl
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

RUTA_OWL = Path(__file__).with_name("mantenimiento_web.owl")
OA = Namespace("https://nicholasph05.github.io/OntoAudit/ontologia#")

PREFIJOS = f"PREFIX oa: <{OA}>\n"


# --------------------------------------------------------------------------
# 1. Cargar y razonar
# --------------------------------------------------------------------------
def razonar(grafo: Graph) -> Graph:
    """Aplica el razonador OWL 2 RL: agrega al grafo todo lo que se puede deducir."""
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(grafo)
    return grafo


def cargar_ontologia(con_razonamiento: bool = True) -> Graph:
    """Lee el archivo .owl (RDF/XML) y, si se pide, lo razona."""
    grafo = Graph()
    grafo.parse(RUTA_OWL, format="xml")
    grafo.bind("oa", OA)
    if con_razonamiento:
        razonar(grafo)
    return grafo


@lru_cache(maxsize=1)
def ontologia() -> Graph:
    """Ontología razonada, cargada una sola vez (caché)."""
    return cargar_ontologia(con_razonamiento=True)


def nombre(uri) -> str:
    """'https://...#ProblemaCargaLenta' -> 'ProblemaCargaLenta'."""
    return str(uri).split("#")[-1]


# --------------------------------------------------------------------------
# 2. Consultas SPARQL
# --------------------------------------------------------------------------
CONSULTA_PROBLEMAS = PREFIJOS + """
SELECT ?problema ?metrica ?umbral ?explicacion ?categoria
       ?practica ?recomendacion ?pasos ?prioridad
WHERE {
    ?problema a oa:Problema ;
              oa:metrica ?metrica ;
              oa:umbral ?umbral ;
              oa:explicacion ?explicacion ;
              oa:incumplePractica ?practica ;
              oa:sugiereAccion ?recomendacion .
    ?recomendacion oa:pasosSolucion ?pasos ;
                   oa:prioridad ?prioridad .
    # La categoría NO está escrita en el .owl: la deduce el razonador
    ?problema a ?categoria .
    VALUES ?categoria { oa:ProblemaSEO oa:ProblemaAccesibilidad oa:ProblemaRendimiento }
}
ORDER BY ?prioridad ?problema
"""


def problemas() -> list[dict]:
    """Todos los problemas conocidos con su explicación y su solución."""
    resultado = []
    for fila in ontologia().query(CONSULTA_PROBLEMAS):
        resultado.append({
            "problema": nombre(fila.problema),
            "metrica": str(fila.metrica),
            "umbral": float(fila.umbral),
            "categoria": nombre(fila.categoria).replace("Problema", ""),
            "explicacion": str(fila.explicacion),
            "practica": nombre(fila.practica),
            "recomendacion": nombre(fila.recomendacion),
            "pasos": str(fila.pasos),
            "prioridad": int(fila.prioridad),
        })
    return resultado


# --------------------------------------------------------------------------
# 3. Detectar problemas a partir de métricas medidas
# --------------------------------------------------------------------------
def detectar_problemas(metricas: dict) -> list[dict]:
    """
    Compara las métricas medidas con los umbrales de la ontología.
    Regla: hay problema si valor > umbral.
    """
    detectados = []
    for p in problemas():
        valor = metricas.get(p["metrica"])
        if valor is not None and valor > p["umbral"]:
            detectados.append({**p, "valor": valor})
    return detectados


# --------------------------------------------------------------------------
# 4. Clasificar un sitio usando el razonador
# --------------------------------------------------------------------------
def clasificar_sitio(url: str, nivel: str, problemas_detectados: list[str]) -> dict:
    """
    Crea el sitio como individuo, lo razona y devuelve lo que se dedujo:
    su clase (SitioCritico...), su estado y las recomendaciones que necesita.
    """
    grafo = cargar_ontologia(con_razonamiento=False)  # copia limpia
    sitio = URIRef(OA["SitioAnalizado"])
    grafo.add((sitio, RDF.type, OA.SitioWeb))
    grafo.add((sitio, OA.url, Literal(url, datatype=XSD.anyURI)))
    grafo.add((sitio, OA.tieneNivel, OA[nivel]))
    for p in problemas_detectados:
        grafo.add((sitio, OA.presentaProblema, OA[p]))
    razonar(grafo)

    clases = {nombre(c) for c in grafo.objects(sitio, RDF.type)}
    estado = grafo.value(sitio, OA.tieneEstado)
    return {
        "clase": next((c for c in ("SitioCritico", "SitioAceptable", "SitioExcelente") if c in clases), None),
        "estado": nombre(estado) if estado else None,
        "recomendaciones": sorted(nombre(r) for r in grafo.objects(sitio, OA.necesitaRecomendacion)),
    }


# --------------------------------------------------------------------------
# Demostración: python -m ontologia.base_conocimiento
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("Triples tras razonar:", len(ontologia()))
    print("\nProblemas que conoce la ontología:")
    for p in problemas():
        print(f"  [{p['categoria']}] {p['problema']}: {p['metrica']} > {p['umbral']}")

    medidas = {"tiempo_carga": 4.8, "img_sin_alt_pct": 25.0, "sin_titulo": 0}
    print("\nMétricas de prueba:", medidas)
    encontrados = detectar_problemas(medidas)
    for p in encontrados:
        print(f"  ! {p['problema']} (valor {p['valor']}) -> {p['pasos']}")

    print("\nClasificación por el razonador:")
    print(" ", clasificar_sitio("https://ejemplo.com", "Urgente", [p["problema"] for p in encontrados]))