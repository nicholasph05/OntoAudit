"""
Etapa 6: valida el informe JSON-LD contra las formas SHACL antes de guardarlo.
"""
from functools import lru_cache
from pathlib import Path

from pyshacl import validate
from rdflib import Graph

from persistencia.jsonld import a_grafo

RUTA_FORMAS = Path(__file__).with_name("formas.ttl")


class InformeInvalido(Exception):
    """El informe no cumple las formas SHACL."""


@lru_cache(maxsize=1)
def formas() -> Graph:
    return Graph().parse(RUTA_FORMAS, format="turtle")


def validar(documento: dict) -> None:
    conforme, _, texto = validate(a_grafo(documento), shacl_graph=formas())
    if not conforme:
        raise InformeInvalido(texto)