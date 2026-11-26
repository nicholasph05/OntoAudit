"""
Etapa 7: API REST de OntoAudit (FastAPI).

    uvicorn api.main:app --reload        -> http://127.0.0.1:8000/docs
"""
import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

import mongomock
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agentes.acl import bitacora
from agentes.analizador import normalizar_url
from agentes.plataforma import Plataforma
from api.seguridad import UrlNoPermitida, verificar_destino
from ontologia.base_conocimiento import problemas
from persistencia.jsonld import a_turtle
from persistencia.repositorio import Repositorio

estado: dict = {}


def crear_repositorio() -> Repositorio:
    """MongoDB real si está disponible; si no, uno simulado en memoria."""
    try:
        repo = Repositorio()
        repo.cliente.admin.command("ping")
        estado["almacen"] = "MongoDB"
    except Exception:
        repo = Repositorio(mongomock.MongoClient())
        estado["almacen"] = "memoria (MongoDB no disponible)"
    return repo


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    repo = crear_repositorio()
    plataforma = Plataforma(guardar=repo.guardar_informe)
    await plataforma.iniciar()
    estado.update(repo=repo, plataforma=plataforma, en_curso={})
    yield
    await plataforma.detener()


app = FastAPI(
    title="OntoAudit API",
    description="Auditoría web con ontologías OWL, lógica difusa y agentes SPADE.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite en desarrollo
    allow_methods=["*"], allow_headers=["*"],
)


class SolicitudAuditoria(BaseModel):
    url: str


# ---------------------------------------------------------------------------
# Auditorías
# ---------------------------------------------------------------------------
@app.post("/api/auditorias", status_code=202)
async def crear_auditoria(solicitud: SolicitudAuditoria):
    """Inicia una auditoría. Responde de inmediato con su id; el resultado llega por /eventos."""
    try:
        url = normalizar_url(solicitud.url)
        await asyncio.to_thread(verificar_destino, url)
    except (ValueError, UrlNoPermitida) as e:
        raise HTTPException(status_code=400, detail=str(e))
    hilo, futuro = estado["plataforma"].analista.solicitar_auditoria(url)
    estado["en_curso"][hilo] = futuro
    return {"auditoria": hilo, "url": url, "eventos": f"/api/auditorias/{hilo}/eventos"}


@app.get("/api/auditorias/{hilo}/eventos")
async def eventos_auditoria(hilo: str):
    """Server-Sent Events: la conversación ACL de los agentes, en vivo."""
    futuro = estado["en_curso"].get(hilo)
    if futuro is None and not bitacora.eventos(hilo):
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")

    async def flujo():
        cola = bitacora.suscribir(hilo)
        try:
            while True:
                try:
                    evento = await asyncio.wait_for(cola.get(), timeout=1)
                    yield f"event: acl\ndata: {json.dumps(evento, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": latido\n\n"   # mantiene viva la conexión
                if futuro is None or (futuro.done() and cola.empty()):
                    break
            resultado = futuro.result() if futuro else {}
            final = {"error": resultado["error"]} if "error" in resultado else {"id": resultado.get("id")}
            yield f"event: fin\ndata: {json.dumps(final, ensure_ascii=False)}\n\n"
        finally:
            bitacora.desuscribir(hilo, cola)
            estado["en_curso"].pop(hilo, None)

    return StreamingResponse(flujo(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/auditorias")
def listar_auditorias(limite: int = 20):
    return estado["repo"].recientes(limite)


@app.get("/api/auditorias/{hilo}")
def obtener_auditoria(hilo: str, request: Request):
    """
    Informe JSON-LD guardado. Con 'Accept: text/turtle' se devuelve en Turtle
    (negociación de contenido, como un servidor de Linked Data).
    """
    documento = estado["repo"].obtener(f"urn:ontoaudit:auditoria:{hilo}")
    if documento is None:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    if "text/turtle" in request.headers.get("accept", ""):
        return PlainTextResponse(a_turtle(documento), media_type="text/turtle")
    return JSONResponse(documento, media_type="application/ld+json")


@app.get("/api/sitios/historial")
def historial_sitio(url: str):
    return estado["repo"].historial(normalizar_url(url))


# ---------------------------------------------------------------------------
# Conocimiento y estado
# ---------------------------------------------------------------------------
@app.get("/api/ontologia/problemas")
def problemas_conocidos():
    """Lo que sabe la ontología: problemas, umbrales, explicaciones y soluciones."""
    return problemas()


@app.get("/api/salud")
def salud():
    return {"estado": "ok", "almacen": estado.get("almacen"),
            "agentes": [str(a.jid) for a in estado["plataforma"].agentes]}


# El dashboard compilado (Etapa 8) se sirve desde la misma API
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="dashboard")