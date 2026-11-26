// Tipos de los datos que entrega la API

export type Nivel = 'AlDia' | 'Preventivo' | 'Urgente'
export type Estado = 'Critico' | 'Aceptable' | 'Excelente'

export interface EventoACL {
  hora: string
  emisor: string
  receptor: string
  performativa: 'request' | 'agree' | 'inform' | 'failure' | string
  resumen: string
}

export interface ProblemaOntologia {
  problema: string
  metrica: string
  umbral: number
  categoria: 'Rendimiento' | 'Accesibilidad' | 'SEO'
  explicacion: string
  practica: string
  recomendacion: string
  pasos: string
  prioridad: number
}

export interface ReglaActivada {
  regla: string
  grado: number
  explicacion: string
}

type Ref = { '@id': string }

// Informe JSON-LD tal como se guarda en MongoDB
export interface InformeJsonLd {
  '@id': string
  'schema:dateCreated': string
  'oa:puntajeDifuso': { '@value': string }
  'oa:analizaSitio': {
    '@id': string
    'oa:tieneNivel': Ref
    'oa:tieneEstado': Ref
    'oa:presentaProblema': Ref[]
    'oa:necesitaRecomendacion': (Ref & { 'oa:pasosSolucion': string; 'oa:prioridad': number })[]
  }
  'schema:variableMeasured': { 'schema:name': string; 'schema:value': number }[]
  'schema:hasPart': {
    'earl:test': Ref
    'earl:result': { 'earl:outcome': Ref; 'earl:info'?: string }
  }[]
  'oa:explicacionDifusa': {
    riesgos: Record<string, number>
    reglas: Record<string, ReglaActivada[]>
  }
}

// Resumen que devuelve /api/auditorias y /api/sitios/historial
export interface ResumenAuditoria {
  '@id': string
  'schema:dateCreated': string
  'oa:puntajeDifuso': { '@value': string }
  'oa:analizaSitio': { '@id'?: string; 'oa:tieneNivel': Ref; 'oa:tieneEstado'?: Ref }
}

export const sinPrefijo = (id: string) => id.replace(/^oa:/, '').replace(/^earl:/, '')
export const idCorto = (id: string) => id.split(':').pop() ?? id