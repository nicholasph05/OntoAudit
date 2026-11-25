"""
Agente Experto: aplica la lógica difusa y consulta la ontología.
"""
import asyncio

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from agentes.acl import JID_NOTIFICADOR, contenido, crear_mensaje, enviar
from fuzzy.motor import evaluar
from ontologia.base_conocimiento import clasificar_sitio, detectar_problemas


def diagnosticar(url: str, metricas: dict) -> dict:
    """Une el veredicto difuso con la explicación semántica de la ontología."""
    difuso = evaluar(metricas)
    problemas = detectar_problemas(metricas)
    semantica = clasificar_sitio(url, difuso["nivel"], [p["problema"] for p in problemas])
    return {
        "url": url,
        "metricas": metricas,
        "difuso": difuso,
        "problemas": problemas,
        "estado": semantica["estado"],
        "clase_inferida": semantica["clase"],
        "recomendaciones_inferidas": semantica["recomendaciones"],
    }


class AgenteExperto(Agent):

    async def setup(self):
        self.solicitantes: dict[str, str] = {}   # hilo -> JID de quien pidió el diagnóstico
        self.add_behaviour(self.Atender())

    class Atender(CyclicBehaviour):

        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return
            performativa = msg.get_metadata("performative")
            if performativa == "request":
                await self.atender_solicitud(msg)
            elif performativa in ("inform", "failure"):
                await self.reenviar_resultado(msg)

        async def atender_solicitud(self, msg):
            hilo = msg.thread
            self.agent.solicitantes[hilo] = str(msg.sender)
            datos = contenido(msg)
            await enviar(self, self._respuesta(msg, "agree", {}), "Acepto: evaluando con lógica difusa y ontología")
            try:
                # Lógica difusa + razonador: cálculo pesado, va en otro hilo
                diagnostico = await asyncio.to_thread(diagnosticar, datos["url"], datos["metricas"])
            except Exception as e:
                await enviar(self, self._respuesta(msg, "failure", {"motivo": str(e)}), f"Error: {e}")
                return
            pedido = crear_mensaje(JID_NOTIFICADOR, "request", diagnostico, hilo)
            await enviar(self, pedido,
                         f"Veredicto {diagnostico['difuso']['nivel']} ({diagnostico['difuso']['puntaje']}/100), "
                         f"estado {diagnostico['estado']}, {len(diagnostico['problemas'])} problemas: guárdalo")

        async def reenviar_resultado(self, msg):
            hilo = msg.thread
            destino = self.agent.solicitantes.pop(hilo, None)
            if destino:
                respuesta = crear_mensaje(destino, msg.get_metadata("performative"), contenido(msg), hilo)
                await enviar(self, respuesta, "Diagnóstico listo" if msg.get_metadata("performative") == "inform"
                             else "No se pudo completar")

        @staticmethod
        def _respuesta(msg, performativa, datos):
            return crear_mensaje(str(msg.sender), performativa, datos, msg.thread)