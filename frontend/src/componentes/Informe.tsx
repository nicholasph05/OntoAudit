import type { InformeJsonLd, ProblemaOntologia } from '../tipos'
import { sinPrefijo } from '../tipos'
import { METRICA, PRUEBA } from '../textos'
import { enlaceDescarga } from '../api'

const PRIORIDAD: Record<number, string> = { 1: 'Prioridad alta', 2: 'Prioridad media', 3: 'Prioridad baja' }

function Problemas({ informe, conocimiento }: { informe: InformeJsonLd; conocimiento: ProblemaOntologia[] }) {
  const detectados = informe['oa:analizaSitio']['oa:presentaProblema'].map((p) => sinPrefijo(p['@id']))
  const lista = conocimiento
    .filter((p) => detectados.includes(p.problema))
    .sort((a, b) => a.prioridad - b.prioridad)

  if (lista.length === 0) {
    return (
      <section className="bloque" aria-labelledby="titulo-problemas">
        <h2 id="titulo-problemas">Qué corregir</h2>
        <p className="vacio">No se detectó ningún problema. El sitio supera las seis pruebas.</p>
      </section>
    )
  }
  return (
    <section className="bloque" aria-labelledby="titulo-problemas">
      <h2 id="titulo-problemas">Qué corregir</h2>
      <ol className="problemas">
        {lista.map((p) => (
          <li key={p.problema} className={`problema prioridad-${p.prioridad}`}>
            <div className="problema-meta">
              <span className="categoria">{p.categoria}</span>
              <span className="prioridad">{PRIORIDAD[p.prioridad]}</span>
            </div>
            <p className="problema-explicacion">{p.explicacion}</p>
            <p className="problema-pasos"><strong>Cómo resolverlo:</strong> {p.pasos}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

function Explicacion({ informe }: { informe: InformeJsonLd }) {
  const { riesgos, reglas } = informe['oa:explicacionDifusa']
  return (
    <section className="bloque" aria-labelledby="titulo-explicacion">
      <h2 id="titulo-explicacion">Por qué este veredicto</h2>
      <p className="ayuda">
        La lógica difusa evalúa cada área por separado y luego combina los tres riesgos.
      </p>
      <div className="riesgos">
        {Object.entries(riesgos).map(([area, valor]) => (
          <div key={area} className="riesgo">
            <div className="riesgo-titulo"><span>{area}</span><span>{valor.toFixed(0)} / 100</span></div>
            <div className="barra" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={valor}
                 aria-label={`Riesgo de ${area}`}>
              <span style={{ width: `${valor}%` }} className={valor >= 65 ? 'alto' : valor >= 35 ? 'medio' : 'bajo'} />
            </div>
            <ul className="reglas">
              {reglas[area]?.map((r) => (
                <li key={r.regla}><span className="grado">{Math.round(r.grado * 100)} %</span> {r.explicacion}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="regla-global">
        <h3>Decisión final</h3>
        <ul className="reglas">
          {reglas['Global']?.map((r) => (
            <li key={r.regla}><span className="grado">{Math.round(r.grado * 100)} %</span> {r.explicacion}</li>
          ))}
        </ul>
      </div>
    </section>
  )
}

function Pruebas({ informe, conocimiento }: { informe: InformeJsonLd; conocimiento: ProblemaOntologia[] }) {
  const nombre = (id: string) => {
    const p = conocimiento.find((c) => c.problema === sinPrefijo(id))
    const texto = PRUEBA[sinPrefijo(id)] ?? sinPrefijo(id)
    return p ? `${texto} (${p.categoria})` : texto
  }
  return (
    <section className="bloque" aria-labelledby="titulo-pruebas">
      <h2 id="titulo-pruebas">Las seis pruebas</h2>
      <p className="ayuda">Resultados en el formato EARL del W3C.</p>
      <ul className="pruebas">
        {informe['schema:hasPart'].map((a) => {
          const aprobo = a['earl:result']['earl:outcome']['@id'] === 'earl:passed'
          return (
            <li key={a['earl:test']['@id']} className={aprobo ? 'aprobada' : 'fallida'}>
              <span className="icono" aria-hidden="true">{aprobo ? '✓' : '✕'}</span>
              <span>{nombre(a['earl:test']['@id'])}</span>
              <span className="visualmente-oculto">{aprobo ? 'aprobada' : 'no aprobada'}</span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function Metricas({ informe }: { informe: InformeJsonLd }) {
  const filas = informe['schema:variableMeasured'].filter((m) => METRICA[m['schema:name']])
  return (
    <section className="bloque" aria-labelledby="titulo-metricas">
      <h2 id="titulo-metricas">Lo que midió el Analista</h2>
      <dl className="metricas">
        {filas.map((m) => (
          <div key={m['schema:name']}>
            <dt>{METRICA[m['schema:name']].nombre}</dt>
            <dd>{m['schema:value']} {METRICA[m['schema:name']].unidad}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

export function Informe({ hilo, informe, conocimiento }: {
  hilo: string; informe: InformeJsonLd; conocimiento: ProblemaOntologia[]
}) {
  return (
    <div className="informe">
      <Problemas informe={informe} conocimiento={conocimiento} />
      <Explicacion informe={informe} />
      <div className="informe-lateral">
        <Pruebas informe={informe} conocimiento={conocimiento} />
        <Metricas informe={informe} />
        <section className="bloque descargas" aria-labelledby="titulo-descargas">
          <h2 id="titulo-descargas">Informe como datos enlazados</h2>
          <p className="ayuda">El mismo informe que se guardó en MongoDB, listo para otras herramientas.</p>
          <a className="boton-secundario" href={enlaceDescarga(hilo)} target="_blank" rel="noreferrer">Ver JSON-LD</a>
          <button className="boton-secundario" onClick={async () => {
            const r = await fetch(enlaceDescarga(hilo), { headers: { Accept: 'text/turtle' } })
            const enlace = document.createElement('a')
            enlace.href = URL.createObjectURL(new Blob([await r.text()], { type: 'text/turtle' }))
            enlace.download = `auditoria-${hilo}.ttl`
            enlace.click()
          }}>Descargar Turtle</button>
        </section>
      </div>
    </div>
  )
}