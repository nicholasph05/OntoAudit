import type { Estado, Nivel } from '../tipos'
import { ESTADO, NIVEL } from '../textos'

/** Medidor semicircular del puntaje difuso (0–100) con sus tres zonas. */
function Medidor({ puntaje, nivel }: { puntaje: number; nivel: Nivel }) {
  const radio = 80
  const arco = Math.PI * radio
  const punto = (valor: number) => {
    const angulo = Math.PI * (1 - valor / 100)
    return [100 + radio * Math.cos(angulo), 100 - radio * Math.sin(angulo)]
  }
  const [x, y] = punto(puntaje)
  const tramo = (desde: number, hasta: number) => ({
    strokeDasharray: `${(arco * (hasta - desde)) / 100} ${arco}`,
    strokeDashoffset: -(arco * desde) / 100,
  })
  return (
    <svg viewBox="0 0 200 118" className="medidor" role="img"
         aria-label={`Puntaje de mantenimiento ${puntaje} de 100`}>
      <path d="M20 100 A80 80 0 0 1 180 100" className="zona zona-aldia" style={tramo(0, 35)} />
      <path d="M20 100 A80 80 0 0 1 180 100" className="zona zona-preventivo" style={tramo(35, 65)} />
      <path d="M20 100 A80 80 0 0 1 180 100" className="zona zona-urgente" style={tramo(65, 100)} />
      <line x1="100" y1="100" x2={x} y2={y} className={`aguja nivel-${nivel}`} />
      <circle cx="100" cy="100" r="5" className="eje" />
    </svg>
  )
}

export function Veredicto({ url, puntaje, nivel, estado }: {
  url: string; puntaje: number; nivel: Nivel; estado: Estado
}) {
  return (
    <section className={`veredicto nivel-${nivel}`} aria-labelledby="titulo-veredicto">
      <h2 id="titulo-veredicto" className="visualmente-oculto">Veredicto</h2>
      <p className="sitio">{url.replace(/^https?:\/\//, '')}</p>
      <div className="veredicto-cuerpo">
        <Medidor puntaje={puntaje} nivel={nivel} />
        <div>
          <p className="nivel">Mantenimiento {NIVEL[nivel].texto.toLowerCase()}</p>
          <p className="puntaje"><strong>{puntaje.toFixed(0)}</strong> de 100 en necesidad de mantenimiento</p>
          <p className="frase">{NIVEL[nivel].frase}</p>
          <p className="inferencia">
            La ontología clasificó el sitio como <strong>{ESTADO[estado]}</strong>.
          </p>
        </div>
      </div>
    </section>
  )
}