"""
Agente Analista: percibe el sitio web y pide el diagnóstico al Experto.
"""
import asyncio
import uuid

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from agentes.acl import JID_EXPERTO, contenido, crear_mensaje, enviar, bitacora
from agentes.analizador import analizar


class AgenteAnalista(Agent):

    async def setup(self):
        self.solicitudes: asyncio.Queue = asyncio.Queue()   # URLs que llegan del usuario
        self.pendientes: dict[str, asyncio.Future] = {}     # hilo -> resultado esperado
        self.add_behaviour(self.Analizar())
        self.add_behaviour(self.EscucharRespuestas())

    def solicitar_auditoria(self, url: str) -> tuple[str, asyncio.Future]:
        """Punto de entrada: el usuario (CLI o API) pide auditar una URL."""
        hilo = uuid.uuid4().hex[:12]
        futuro = asyncio.get_running_loop().create_future()
        self.pendientes[hilo] = futuro
        self.solicitudes.put_nowait((hilo, url))
        return hilo, futuro

    class Analizar(CyclicBehaviour):
        """Toma una URL, mide sus métricas y envía REQUEST al Experto."""

        async def run(self):
            hilo, url = await self.agent.solicitudes.get()
            bitacora.registrar(hilo, "usuario", str(self.agent.jid), "request", f"Auditar {url}")
            try:
                # analizar() hace peticiones HTTP (bloqueantes): va en otro hilo
                metricas = await asyncio.to_thread(analizar, url)
            except Exception as e:
                bitacora.registrar(hilo, str(self.agent.jid), "usuario", "failure", str(e))
                self.agent.pendientes.pop(hilo).set_result({"error": str(e)})
                return
            msg = crear_mensaje(JID_EXPERTO, "request", {"url": url, "metricas": metricas}, hilo)
            await enviar(self, msg,
                         f"Métricas de {url}: {metricas['tiempo_carga']} s, "
                         f"{metricas['img_sin_alt_pct']} % imágenes sin alt, "
                         f"{metricas['errores_sintaxis']} errores HTML")

    class EscucharRespuestas(CyclicBehaviour):
        """Recibe AGREE / INFORM / FAILURE del Experto y entrega el resultado."""

        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return
            performativa = msg.get_metadata("performative")
            futuro = self.agent.pendientes.get(msg.thread)
            if performativa in ("inform", "failure") and futuro and not futuro.done():
                datos = contenido(msg)
                futuro.set_result(datos if performativa == "inform" else {"error": datos.get("motivo")})
                self.agent.pendientes.pop(msg.thread, None)