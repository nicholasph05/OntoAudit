import type { EventoACL } from '../tipos'
import { AGENTES, NOMBRE_AGENTE, PERFORMATIVA, TAREA_AGENTE } from '../textos'

/**
 * Diagrama de secuencia en vivo: cada mensaje ACL es una flecha
 * entre las líneas de vida de los agentes.
 */
export function Conversacion({ eventos, activa }: { eventos: EventoACL[]; activa: boolean }) {
  const columna = (agente: string) => Math.max(0, AGENTES.indexOf(agente as (typeof AGENTES)[number]))

  return (
    <section className="conversacion" aria-labelledby="titulo-conversacion">
      <h2 id="titulo-conversacion">Conversación de los agentes</h2>
      <p className="ayuda">
        Cada flecha es un mensaje FIPA-ACL real entre los agentes SPADE.
      </p>

      <div className="secuencia" role="list" aria-live="polite">
        <div className="secuencia-cabecera" aria-hidden="true">
          {AGENTES.map((a) => (
            <div key={a} className={`actor actor-${a}`}>
              <strong>{NOMBRE_AGENTE[a]}</strong>
              <span>{TAREA_AGENTE[a]}</span>
            </div>
          ))}
        </div>

        <div className="secuencia-cuerpo">
          {AGENTES.map((a, i) => (
            <span key={a} className="linea-vida" style={{ left: `${(i + 0.5) * 25}%` }} aria-hidden="true" />
          ))}

          {eventos.map((e, i) => {
            const desde = columna(e.emisor)
            const hacia = columna(e.receptor)
            const izquierda = Math.min(desde, hacia)
            const ancho = Math.abs(hacia - desde)
            return (
              <div key={i} className={`mensaje performativa-${e.performativa}`} role="listitem">
                <div
                  className={`flecha ${hacia < desde ? 'hacia-izquierda' : 'hacia-derecha'}`}
                  style={{ left: `${(izquierda + 0.5) * 25}%`, width: `${ancho * 25}%` }}
                >
                  <span className="etiqueta-performativa">{PERFORMATIVA[e.performativa] ?? e.performativa}</span>
                </div>
                <p className="resumen">
                  <span className="visualmente-oculto">
                    {NOMBRE_AGENTE[e.emisor]} {PERFORMATIVA[e.performativa]} a {NOMBRE_AGENTE[e.receptor]}:{' '}
                  </span>
                  {e.resumen}
                </p>
              </div>
            )
          })}

          {activa && (
            <div className="mensaje pensando" aria-hidden="true">
              <p className="resumen">Esperando el siguiente mensaje…</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}