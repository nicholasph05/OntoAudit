"""
Prueba de integración: levanta el servidor XMPP y los 3 agentes, y verifica
que se comuniquen con mensajes ACL siguiendo el protocolo FIPA-Request.

El servidor XMPP embebido solo puede iniciarse una vez por proceso, por eso
los dos escenarios se prueban con la misma plataforma.
"""
import asyncio

from agentes.acl import bitacora
from agentes.agente_notificador import INFORMES_EN_MEMORIA
from agentes.plataforma import Plataforma
from tests.test_analizador import sitio  # noqa: F401  (reutiliza el sitio web local)


def test_los_agentes_conversan_por_acl(sitio):  # noqa: F811
    async def flujo():
        plataforma = Plataforma()
        await plataforma.iniciar()
        try:
            exito = await plataforma.auditar(sitio + "/", espera=60)
            prohibido = await plataforma.auditar(sitio + "/privado/", espera=60)
        finally:
            await plataforma.detener()
        return exito, prohibido

    exito, prohibido = asyncio.run(flujo())

    # 1. Auditoría normal: diagnóstico completo y guardado
    assert exito["difuso"]["nivel"] in ("AlDia", "Preventivo", "Urgente")
    assert exito["estado"] in ("Critico", "Aceptable", "Excelente")
    assert any(p["problema"] == "ProblemaImagenesSinAlt" for p in exito["problemas"])
    assert INFORMES_EN_MEMORIA[-1]["auditoria"] == exito["auditoria"]

    conversacion = [(e["emisor"], e["receptor"], e["performativa"])
                    for e in bitacora.eventos(exito["auditoria"])]
    assert conversacion == [
        ("usuario", "analista", "request"),
        ("analista", "experto", "request"),
        ("experto", "analista", "agree"),
        ("experto", "notificador", "request"),
        ("notificador", "experto", "inform"),
        ("experto", "analista", "inform"),
    ]

    # 2. Sitio que prohíbe robots: termina en 'failure'
    assert "robots.txt" in prohibido["error"]
    assert bitacora.eventos(prohibido["auditoria"])[-1]["performativa"] == "failure"