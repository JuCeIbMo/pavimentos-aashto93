import type { Proyecto, Resultado } from './tipos'

async function pedir<T>(url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
  if (!r.ok) {
    let msg = `Error ${r.status}`
    try { msg = (await r.json()).detail ?? msg } catch { /* sin cuerpo JSON */ }
    throw new Error(msg)
  }
  return r.json() as Promise<T>
}

export const api = {
  inicial: () => pedir<Proyecto>('/api/proyecto/inicial'),
  nuevo: () => pedir<Proyecto>('/api/proyecto/nuevo'),
  resolver: (proyecto: Proyecto) => pedir<Resultado>('/api/resolver', { proyecto }),
  ejemplos: () => pedir<{ id: string; fuente: Fuente; proyecto: Proyecto }[]>('/api/ejemplos'),
  catalogo: () => pedir<{ fuente: string; opciones: OpcionCatalogo[] }>('/api/catalogo'),
  referencias: () => pedir<Referencias>('/api/referencias'),
  validacion: () => pedir<Validacion[]>('/api/validacion'),
  variables: () => pedir<VariableSens[]>('/api/sensibilidad/variables'),
  barrido: (proyecto: Proyecto, variable: string, desde?: number, hasta?: number) =>
    pedir<Barrido>('/api/sensibilidad/barrido', { proyecto, variable, desde, hasta, n: 41 }),
  tornado: (proyecto: Proyecto, variacion: number, metrica: 'sn' | 'espesor') =>
    pedir<FilaTornado[]>('/api/sensibilidad/tornado', { proyecto, variacion, metrica }),
  escenarios: (proyecto: Proyecto, escenarios: { nombre: string; cambios: Record<string, number> }[]) =>
    pedir<FilaEscenario[]>('/api/sensibilidad/escenarios', { proyecto, escenarios }),
  curvaClima: (proyecto: Proyecto, t_max: number) =>
    pedir<{ t: number; sw: number; fh: number; total: number }[]>('/api/clima/curva', { proyecto, t_max }),
}

/** Descarga un archivo generado por la API (PDF o Excel). */
export async function descargar(tipo: 'pdf' | 'excel', proyecto: Proyecto) {
  const r = await fetch(`/api/exportar/${tipo}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ proyecto }),
  })
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? `Error ${r.status}`)
  const blob = await r.blob()
  const cd = r.headers.get('Content-Disposition') ?? ''
  const utf = /filename\*=UTF-8''([^;]+)/.exec(cd)
  const simple = /filename="([^"]+)"/.exec(cd)
  const nombre = utf ? decodeURIComponent(utf[1]) : simple ? simple[1] : `proyecto.${tipo === 'pdf' ? 'pdf' : 'xlsx'}`
  guardarBlob(blob, nombre)
}

export function guardarBlob(blob: Blob, nombre: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = nombre
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export interface Fuente { titulo: string; tipo: string; referencia: string }
export interface OpcionCatalogo {
  etiqueta: string; nombre: string; pesado: boolean; ejes: [string, number][]; unidad: 't' | null; fuente: string | null
}
export interface Ecuacion { latex: string; fuente: string; ref?: string; explica: string }
export interface Referencias {
  referencias: Record<string, string>
  ecuaciones: Record<string, Ecuacion>
  minimos_aashto: { w_max: number | null; carpeta: number; base: number }[]
}
export interface FilaValidacion {
  clave: string; etiqueta: string; unidad?: string; valor: number; app: number | null; dif_rel: number | null
  tol_rel: number; cumple: boolean; tipo?: string; nota?: string
}
export interface Validacion {
  id: string; fuente: Fuente; filas: FilaValidacion[]; aprobado: boolean; n_ok: number; n_total: number; proyecto: Proyecto
}
export interface VariableSens { clave: string; etiqueta: string; unidad: string; minimo: number; maximo: number; explicacion: string }
export interface PuntoBarrido {
  x: number; ok: boolean; sn_requerido: number; sn_total: number; d1: number; d2: number; d3: number
  espesor_total: number; unidad: string; periodo: number | null
}
export interface Barrido { x0: number; desde: number; hasta: number; puntos: PuntoBarrido[] }
export interface FilaTornado {
  clave: string; etiqueta: string; x0: number; x_lo: number; x_hi: number; sn_lo: number; sn_hi: number
  esp_lo: number; esp_hi: number; rango_sn: number; rango_esp: number; sn_base: number; esp_base: number; unidad: string
}
export interface FilaEscenario {
  escenario: string; ok: boolean; sn_requerido?: number; d1?: number; d2?: number; d3?: number; espesor_total?: number
  unidad?: string; w18?: number; mr?: number; r_pct?: number; so?: number; dpsi?: number; sn_adoptado?: number
  periodo?: number | null; avisos: string[]
}
