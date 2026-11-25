"""
Agente Notificador: estructura el informe final y lo guarda.

En la Etapa 5 guarda en memoria; en la Etapa 6 se le conecta MongoDB + JSON-LD
sin cambiar al agente (recibe la función 'guardar' desde afuera).
"""
import asyncio
from datetime import datetime, timezone
from typing import Callable

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from agentes.acl import contenido, crear_mensaje, enviar

INFORMES_EN_MEMORIA: list[dict] = []


def guardar_en_memoria(informe: dict) -> str:
    INFORMES_EN_MEMORIA.append(informe)
    return str(len(INFORMES_EN_MEMORIA))


class AgenteNotificador(Agent):

    def __init__(self, *args, guardar: Callable[[dict], str] = guardar_en_memoria, **kwargs):
        super().__init__(*args, **kwargs)
        self.guardar = guardar

    async def setup(self):
        self.add_behaviour(self.Guardar())

    class Guardar(CyclicBehaviour):

        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg or msg.get_metadata("performative") != "request":
                return
            informe = {
                **contenido(msg),
                "auditoria": msg.thread,
                "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            try:
                identificador = await asyncio.to_thread(self.agent.guardar, informe)
                informe["id"] = identificador
                respuesta = crear_mensaje(str(msg.sender), "inform", informe, msg.thread)
                resumen = f"Informe guardado (id {identificador})"
            except Exception as e:
                respuesta = crear_mensaje(str(msg.sender), "failure", {"motivo": str(e)}, msg.thread)
                resumen = f"No se pudo guardar: {e}"
            await enviar(self, respuesta, resumen)