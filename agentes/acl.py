"""
Mensajes ACL (FIPA) compartidos por los agentes y la bitácora de la conversación.

Protocolo FIPA-Request usado en OntoAudit:

  Analista ──request──► Experto            "evalúa estas métricas"
  Analista ◄──agree──── Experto            "acepto, estoy en ello"
           Experto ──request──► Notificador "guarda este diagnóstico"
           Experto ◄──inform─── Notificador "guardado con id X"
  Analista ◄──inform─── Experto            "diagnóstico listo"
  (si algo falla, la respuesta es 'failure' con el motivo)
"""
import asyncio
import json
from datetime import datetime, timezone

from spade.message import Message

DOMINIO = "localhost"
JID_ANALISTA = f"analista@{DOMINIO}"
JID_EXPERTO = f"experto@{DOMINIO}"
JID_NOTIFICADOR = f"notificador@{DOMINIO}"
CLAVE = "ontoaudit"
ONTOLOGIA = "https://nicholasph05.github.io/OntoAudit/ontologia"
PROTOCOLO = "fipa-request"


def crear_mensaje(destino: str, performativa: str, contenido: dict, hilo: str) -> Message:
    msg = Message(to=destino, body=json.dumps(contenido, ensure_ascii=False), thread=hilo)
    msg.set_metadata("performative", performativa)
    msg.set_metadata("protocol", PROTOCOLO)
    msg.set_metadata("ontology", ONTOLOGIA)
    msg.set_metadata("language", "application/json")
    return msg


def contenido(msg: Message) -> dict:
    return json.loads(msg.body)


class Bitacora:
    """
    Registro de todos los mensajes ACL, agrupado por auditoría (hilo).
    Permite que el dashboard vea la conversación en vivo (suscripción).
    """

    def __init__(self):
        self._eventos: dict[str, list[dict]] = {}
        self._suscriptores: dict[str, list[asyncio.Queue]] = {}

    def registrar(self, hilo: str, emisor: str, receptor: str, performativa: str, resumen: str):
        evento = {
            "hora": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "emisor": emisor.split("@")[0],
            "receptor": receptor.split("@")[0],
            "performativa": performativa,
            "resumen": resumen,
        }
        self._eventos.setdefault(hilo, []).append(evento)
        for cola in self._suscriptores.get(hilo, []):
            cola.put_nowait(evento)

    def eventos(self, hilo: str) -> list[dict]:
        return list(self._eventos.get(hilo, []))

    def suscribir(self, hilo: str) -> asyncio.Queue:
        cola: asyncio.Queue = asyncio.Queue()
        for evento in self.eventos(hilo):   # lo que ya pasó
            cola.put_nowait(evento)
        self._suscriptores.setdefault(hilo, []).append(cola)
        return cola

    def desuscribir(self, hilo: str, cola: asyncio.Queue):
        if cola in self._suscriptores.get(hilo, []):
            self._suscriptores[hilo].remove(cola)


bitacora = Bitacora()


async def enviar(comportamiento, msg: Message, resumen: str):
    """Envía el mensaje y lo anota en la bitácora."""
    await comportamiento.send(msg)
    bitacora.registrar(msg.thread, str(comportamiento.agent.jid), str(msg.to),
                       msg.get_metadata("performative"), resumen)