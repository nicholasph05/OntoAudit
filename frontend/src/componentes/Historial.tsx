import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Nivel, ResumenAuditoria } from '../tipos'
import { idCorto, sinPrefijo } from '../tipos'
import { NIVEL, fecha } from '../textos'

function Tendencia({ puntos }: { puntos: ResumenAuditoria[] }) {
  if (puntos.length < 2) {
    return <p className="ayuda">Audita este sitio otra vez para ver cómo evoluciona.</p>
  }
  const ancho = 320, alto = 90
  const valores = puntos.map((p) => Number(p['oa:puntajeDifuso']['@value']))
  const x = (i: number) => 10 + (i * (ancho - 20)) / (valores.length - 1)
  const y = (v: number) => alto - 8 - (v / 100) * (alto - 16)
  const trazo = valores.map((v, i) => `${i ? 'L' : 'M'}${x(i)},${y(v)}`).join(' ')
  return (
    <svg viewBox={`0 0 ${ancho} ${alto}`} className="tendencia" role="img"
         aria-label={`Evolución del puntaje: ${valores.join(', ')}`}>
      <rect x="0" y={y(100)} width={ancho} height={y(65) - y(100)} className="banda-urgente" />
      <rect x="0" y={y(35)} width={ancho} height={y(0) - y(35)} className="banda-aldia" />
      <path d={trazo} className="trazo" />
      {valores.map((v, i) => <circle key={i} cx={x(i)} cy={y(v)} r="3.5" className="punto" />)}
    </svg>
  )
}

export function Historial({ alAbrir }: { alAbrir: (hilo: string) => void }) {
  const [lista, setLista] = useState<ResumenAuditoria[] | null>(null)
  const [error, setError] = useState('')
  const [sitio, setSitio] = useState<string | null>(null)
  const [puntos, setPuntos] = useState<ResumenAuditoria[]>([])

  useEffect(() => {
    api.recientes().then(setLista).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (sitio) api.historial(sitio).then(setPuntos).catch(() => setPuntos([]))
  }, [sitio])

  if (error) return <p className="error" role="alert">{error}</p>
  if (!lista) return <p className="ayuda">Cargando auditorías…</p>
  if (lista.length === 0) return <p className="vacio">Aún no hay auditorías. Audita tu primer sitio para empezar el historial.</p>

  return (
    <div className="historial">
      <table>
        <caption className="visualmente-oculto">Auditorías recientes</caption>
        <thead>
          <tr><th scope="col">Sitio</th><th scope="col">Fecha</th><th scope="col">Veredicto</th><th scope="col">Puntaje</th><th scope="col"><span className="visualmente-oculto">Acciones</span></th></tr>
        </thead>
        <tbody>
          {lista.map((a) => {
            const url = a['oa:analizaSitio']['@id'] ?? ''
            const nivel = sinPrefijo(a['oa:analizaSitio']['oa:tieneNivel']['@id']) as Nivel
            return (
              <tr key={a['@id']} className={sitio === url ? 'seleccionada' : ''}>
                <td><button className="enlace" onClick={() => setSitio(url)}>{url.replace(/^https?:\/\//, '')}</button></td>
                <td>{fecha(a['schema:dateCreated'])}</td>
                <td><span className={`insignia nivel-${nivel}`}>{NIVEL[nivel].texto}</span></td>
                <td>{Number(a['oa:puntajeDifuso']['@value']).toFixed(0)}</td>
                <td><button className="boton-secundario" onClick={() => alAbrir(idCorto(a['@id']))}>Ver informe</button></td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {sitio && (
        <aside className="bloque" aria-labelledby="titulo-tendencia">
          <h2 id="titulo-tendencia">Evolución de {sitio.replace(/^https?:\/\//, '')}</h2>
          <Tendencia puntos={puntos} />
        </aside>
      )}
    </div>
  )
}