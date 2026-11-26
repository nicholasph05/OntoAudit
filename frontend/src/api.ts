import type { EventoACL, InformeJsonLd, ProblemaOntologia, ResumenAuditoria } from './tipos'

async function pedir<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  const r = await fetch(ruta, opciones)
  if (!r.ok) {
    const cuerpo = await r.json().catch(() => ({}))
    throw new Error(cuerpo.detail ?? `Error ${r.status} en ${ruta}`)
  }
  return r.json()
}

export const api = {
  salud: () => pedir<{ estado: string; almacen: string; agentes: string[] }>('/api/salud'),
  problemas: () => pedir<ProblemaOntologia[]>('/api/ontologia/problemas'),
  recientes: () => pedir<ResumenAuditoria[]>('/api/auditorias?limite=30'),
  historial: (url: string) => pedir<ResumenAuditoria[]>(`/api/sitios/historial?url=${encodeURIComponent(url)}`),
  informe: (hilo: string) => pedir<InformeJsonLd>(`/api/auditorias/${hilo}`),
  iniciar: (url: string) =>
    pedir<{ auditoria: string; url: string }>('/api/auditorias', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    }),
}

/** Escucha la conversación ACL en vivo (Server-Sent Events). */
export function escucharAuditoria(
  hilo: string,
  alEvento: (e: EventoACL) => void,
  alTerminar: (fin: { id?: string; error?: string }) => void,
): () => void {
  const fuente = new EventSource(`/api/auditorias/${hilo}/eventos`)
  fuente.addEventListener('acl', (m) => alEvento(JSON.parse((m as MessageEvent).data)))
  fuente.addEventListener('fin', (m) => {
    fuente.close()
    alTerminar(JSON.parse((m as MessageEvent).data))
  })
  fuente.onerror = () => {
    fuente.close()
    alTerminar({ error: 'Se perdió la conexión con el servidor.' })
  }
  return () => fuente.close()
}

export const enlaceDescarga = (hilo: string) => `/api/auditorias/${hilo}`