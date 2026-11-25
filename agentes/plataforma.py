"""
Arranca el servidor XMPP embebido y los tres agentes.

Uso por consola:
    python -m agentes.plataforma https://example.com
"""
import asyncio
import contextlib

from pyjabber.server import Server
from pyjabber.server_parameters import Parameters
from spade.container import Container

from agentes.acl import CLAVE, DOMINIO, JID_ANALISTA, JID_EXPERTO, JID_NOTIFICADOR, bitacora
from agentes.agente_analista import AgenteAnalista
from agentes.agente_experto import AgenteExperto
from agentes.agente_notificador import AgenteNotificador, guardar_en_memoria


class Plataforma:

    def __init__(self, guardar=guardar_en_memoria):
        self.guardar = guardar
        self._servidor_tarea = None
        self.agentes = []

    async def iniciar(self):
        import loguru
        loguru.logger.remove()   # el servidor XMPP es muy verboso
        Container().reset()      # el contenedor de SPADE usa el event loop actual
        servidor = Server(Parameters(host=DOMINIO, database_in_memory=True))
        self._servidor_tarea = asyncio.create_task(servidor.start())
        await asyncio.wait_for(servidor.ready.wait(), timeout=15)

        self.notificador = AgenteNotificador(JID_NOTIFICADOR, CLAVE, guardar=self.guardar)
        self.experto = AgenteExperto(JID_EXPERTO, CLAVE)
        self.analista = AgenteAnalista(JID_ANALISTA, CLAVE)
        self.agentes = [self.notificador, self.experto, self.analista]
        for agente in self.agentes:
            await agente.start(auto_register=True)

    async def auditar(self, url: str, espera: float = 90) -> dict:
        hilo, futuro = self.analista.solicitar_auditoria(url)
        resultado = await asyncio.wait_for(futuro, timeout=espera)
        return {"auditoria": hilo, **resultado}

    async def detener(self):
        for agente in self.agentes:
            with contextlib.suppress(Exception):
                await agente.stop()
        if self._servidor_tarea:
            self._servidor_tarea.cancel()
            with contextlib.suppress(BaseException):
                await asyncio.wait_for(self._servidor_tarea, timeout=3)


def guardado_disponible():
    """Usa MongoDB si está encendido; si no, guarda en memoria."""
    try:
        from persistencia.repositorio import Repositorio
        repo = Repositorio()
        repo.cliente.admin.command("ping")
        print("Guardando en MongoDB (base 'ontoaudit', colección 'auditorias')")
        return repo.guardar_informe
    except Exception as e:
        print(f"MongoDB no disponible ({type(e).__name__}); se guarda en memoria")
        return guardar_en_memoria


async def _demo(url: str):
    plataforma = Plataforma(guardar=guardado_disponible())
    await plataforma.iniciar()
    try:
        r = await plataforma.auditar(url)
    finally:
        await plataforma.detener()

    print("\nConversación ACL:")
    for e in bitacora.eventos(r["auditoria"]):
        print(f"  {e['emisor']:>11} → {e['receptor']:<11} [{e['performativa']:^7}] {e['resumen']}")
    if "error" in r:
        print("\nError:", r["error"])
        return
    print(f"\nVeredicto: {r['difuso']['nivel']} ({r['difuso']['puntaje']}/100) — estado {r['estado']}")
    for p in r["problemas"]:
        print(f"  • [{p['categoria']}] {p['explicacion']}\n      → {p['pasos']}")


if __name__ == "__main__":
    import sys
    asyncio.run(_demo(sys.argv[1] if len(sys.argv) > 1 else "https://example.com"))