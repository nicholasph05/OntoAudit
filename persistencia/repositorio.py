"""
Etapa 6: guarda y consulta los informes JSON-LD en MongoDB.
"""
import os

from pymongo import DESCENDING, MongoClient

from persistencia.jsonld import a_jsonld
from persistencia.validacion import validar

URI_MONGO = os.getenv("MONGO_URI", "mongodb://localhost:27017")

CAMPO_SITIO = "oa:analizaSitio.@id"
CAMPO_FECHA = "schema:dateCreated"


class Repositorio:

    def __init__(self, cliente: MongoClient | None = None, base: str = "ontoaudit"):
        self.cliente = cliente or MongoClient(URI_MONGO, serverSelectionTimeoutMS=3000)
        self.coleccion = self.cliente[base]["auditorias"]
        self.coleccion.create_index("@id", unique=True)
        self.coleccion.create_index([(CAMPO_SITIO, 1), (CAMPO_FECHA, DESCENDING)])

    def guardar_informe(self, informe: dict) -> str:
        """Usado por el Agente Notificador: convierte, valida y guarda."""
        documento = a_jsonld(informe)
        validar(documento)                 # si no cumple SHACL, no se guarda
        self.coleccion.insert_one(documento)
        return documento["@id"]

    def obtener(self, id_auditoria: str) -> dict | None:
        return self.coleccion.find_one({"@id": id_auditoria}, {"_id": 0})

    def recientes(self, limite: int = 20) -> list[dict]:
        proyeccion = {"_id": 0, "@id": 1, CAMPO_FECHA: 1, "oa:puntajeDifuso": 1,
                      "oa:analizaSitio.@id": 1, "oa:analizaSitio.oa:tieneNivel": 1,
                      "oa:analizaSitio.oa:tieneEstado": 1}
        return list(self.coleccion.find({}, proyeccion).sort(CAMPO_FECHA, DESCENDING).limit(limite))

    def historial(self, url: str) -> list[dict]:
        """Evolución de un mismo sitio en el tiempo."""
        proyeccion = {"_id": 0, "@id": 1, CAMPO_FECHA: 1, "oa:puntajeDifuso": 1,
                      "oa:analizaSitio.oa:tieneNivel": 1}
        return list(self.coleccion.find({CAMPO_SITIO: url}, proyeccion).sort(CAMPO_FECHA, 1))


if __name__ == "__main__":
    import json
    repo = Repositorio()
    print("Auditorías guardadas:", repo.coleccion.count_documents({}))
    for doc in repo.recientes(5):
        print(json.dumps(doc, ensure_ascii=False))