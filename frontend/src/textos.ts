import type { Estado, Nivel } from './tipos'

export const NIVEL: Record<Nivel, { texto: string; frase: string }> = {
  AlDia: { texto: 'Al día', frase: 'El sitio está en buen estado. Basta con revisarlo de vez en cuando.' },
  Preventivo: { texto: 'Preventivo', frase: 'Conviene programar mantenimiento antes de que los problemas crezcan.' },
  Urgente: { texto: 'Urgente', frase: 'Hay problemas que ya afectan a tus visitantes. Atiéndelos pronto.' },
}

export const ESTADO: Record<Estado, string> = {
  Critico: 'Crítico',
  Aceptable: 'Aceptable',
  Excelente: 'Excelente',
}

export const AGENTES = ['usuario', 'analista', 'experto', 'notificador'] as const

export const NOMBRE_AGENTE: Record<string, string> = {
  usuario: 'Tú',
  analista: 'Analista',
  experto: 'Experto',
  notificador: 'Notificador',
}

export const TAREA_AGENTE: Record<string, string> = {
  usuario: 'pides la auditoría',
  analista: 'mide la página',
  experto: 'razona y diagnostica',
  notificador: 'guarda el informe',
}

export const PERFORMATIVA: Record<string, string> = {
  request: 'pide',
  agree: 'acepta',
  inform: 'informa',
  failure: 'falla',
}

export const METRICA: Record<string, { nombre: string; unidad: string }> = {
  tiempo_carga: { nombre: 'Tiempo de carga', unidad: 's' },
  peso_pagina_mb: { nombre: 'Peso de la página', unidad: 'MB' },
  img_sin_alt_pct: { nombre: 'Imágenes sin texto alternativo', unidad: '%' },
  errores_sintaxis: { nombre: 'Errores de HTML', unidad: '' },
  total_imagenes: { nombre: 'Imágenes en la página', unidad: '' },
  recursos_descargados: { nombre: 'Archivos descargados', unidad: '' },
}

export const fecha = (iso: string) =>
  new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

export const PRUEBA: Record<string, string> = {
  ProblemaCargaLenta: 'Carga en menos de 3 segundos',
  ProblemaPaginaPesada: 'Pesa menos de 2 MB',
  ProblemaImagenesSinAlt: 'Todas las imágenes tienen texto alternativo',
  ProblemaErroresSintaxis: 'HTML con pocos errores',
  ProblemaSinTitulo: 'Tiene título',
  ProblemaSinMetaDescripcion: 'Tiene descripción para buscadores',
}