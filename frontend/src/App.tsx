import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { api, escucharAuditoria } from './api'
import type { Estado, EventoACL, InformeJsonLd, Nivel, ProblemaOntologia } from './tipos'
import { sinPrefijo } from './tipos'
import { Conversacion } from './componentes/Conversacion'
import { Veredicto } from './componentes/Veredicto'
import { Informe } from './componentes/Informe'
import { Historial } from './componentes/Historial'

type Fase = 'inicio' | 'auditando' | 'listo' | 'error'
type Vista = 'auditar' | 'historial'

const EJEMPLOS = ['example.com', 'www.politecnicojic.edu.co', 'es.wikipedia.org']

export default function App() {
  const [vista, setVista] = useState<Vista>('auditar')
  const [url, setUrl] = useState('')
  const [fase, setFase] = useState<Fase>('inicio')
  const [error, setError] = useState('')
  const [eventos, setEventos] = useState<EventoACL[]>([])
  const [hilo, setHilo] = useState('')
  const [informe, setInforme] = useState<InformeJsonLd | null>(null)
  const [conocimiento, setConocimiento] = useState<ProblemaOntologia[]>([])
  const [salud, setSalud] = useState<{ almacen: string; agentes: string[] } | null>(null)
  const detener = useRef<() => void>(() => {})

  useEffect(() => {
    api.salud().then(setSalud).catch(() => setSalud(null))
    api.problemas().then(setConocimiento).catch(() => {})
    return () => detener.current()
  }, [])

  async function abrirInforme(id: string) {
    setHilo(id)
    setInforme(await api.informe(id))
    setFase('listo')
  }

  async function auditar(ev: FormEvent) {
    ev.preventDefault()
    detener.current()
    setEventos([]); setInforme(null); setError(''); setFase('auditando')
    try {
      const { auditoria } = await api.iniciar(url)
      setHilo(auditoria)
      detener.current = escucharAuditoria(
        auditoria,
        (e) => setEventos((previos) => [...previos, e]),
        async (fin) => {
          if (fin.error) { setError(fin.error); setFase('error'); return }
          await abrirInforme(auditoria)
        },
      )
    } catch (e) {
      setError((e as Error).message); setFase('error')
    }
  }

  function verDesdeHistorial(id: string) {
    setEventos([]); setError(''); setVista('auditar')
    abrirInforme(id).catch((e) => { setError(e.message); setFase('error') })
  }

  const sitio = informe?.['oa:analizaSitio']

  return (
    <>
      <a className="saltar" href="#contenido">Saltar al contenido</a>
      <header className="cabecera">
        <div className="marca">
          <img src="/favicon.svg" alt="" width="28" height="28" />
          <span>OntoAudit</span>
        </div>
        <nav aria-label="Secciones">
          <button aria-current={vista === 'auditar' ? 'page' : undefined} onClick={() => setVista('auditar')}>Auditar</button>
          <button aria-current={vista === 'historial' ? 'page' : undefined} onClick={() => setVista('historial')}>Historial</button>
        </nav>
        <p className={`salud ${salud ? 'en-linea' : 'sin-conexion'}`}>
          {salud ? `${salud.agentes.length} agentes en línea, datos en ${salud.almacen}` : 'Servidor sin conexión'}
        </p>
      </header>

      <main id="contenido">
        {vista === 'historial' ? (
          <section className="pagina">
            <h1 className="titulo-pagina">Historial de auditorías</h1>
            <Historial alAbrir={verDesdeHistorial} />
          </section>
        ) : (
          <>
            <section className="portada">
              <h1>¿Tu sitio web necesita mantenimiento?</h1>
              <p className="entradilla">
                Tres agentes inteligentes miden la página, razonan con una ontología y lógica difusa,
                y te dicen qué corregir primero.
              </p>
              <form onSubmit={auditar} className="formulario">
                <label htmlFor="url">Dirección del sitio</label>
                <div className="campo">
                  <input id="url" type="text" inputMode="url" autoComplete="url" placeholder="ejemplo.com"
                         value={url} onChange={(e) => setUrl(e.target.value)} required
                         disabled={fase === 'auditando'} />
                  <button type="submit" disabled={fase === 'auditando' || !url.trim()}>
                    {fase === 'auditando' ? 'Auditando…' : 'Auditar sitio'}
                  </button>
                </div>
                <p className="ejemplos">
                  Prueba con{' '}
                  {EJEMPLOS.map((e, i) => (
                    <span key={e}>
                      <button type="button" className="enlace" onClick={() => setUrl(e)}>{e}</button>
                      {i < EJEMPLOS.length - 1 ? ', ' : ''}
                    </span>
                  ))}
                </p>
              </form>
            </section>

            {fase === 'error' && (
              <p className="error" role="alert"><strong>No se pudo completar la auditoría.</strong> {error}</p>
            )}

            {(eventos.length > 0 || fase === 'auditando') && (
              <Conversacion eventos={eventos} activa={fase === 'auditando'} />
            )}

            {fase === 'listo' && informe && sitio && (
              <>
                <Veredicto
                  url={sitio['@id']}
                  puntaje={Number(informe['oa:puntajeDifuso']['@value'])}
                  nivel={sinPrefijo(sitio['oa:tieneNivel']['@id']) as Nivel}
                  estado={sinPrefijo(sitio['oa:tieneEstado']['@id']) as Estado}
                />
                <Informe hilo={hilo} informe={informe} conocimiento={conocimiento} />
              </>
            )}
          </>
        )}
      </main>

      <footer className="pie">
        <p>
          Proyecto de Web Semántica: ontología OWL, lógica difusa (scikit-fuzzy), agentes SPADE
          y datos enlazados JSON-LD.{' '}
          <a href="https://github.com/nicholasph05/OntoAudit">Código en GitHub</a>
        </p>
      </footer>
    </>
  )
}