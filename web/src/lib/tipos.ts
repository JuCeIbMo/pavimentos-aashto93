// Espejo de pavimentos/modelo.py (ProyectoFlexible.to_dict) y del resultado del resolver.

export type TipoEje = 'simple' | 'tandem' | 'tridem'
export type Eje = [TipoEje, number]

export interface Vehiculo {
  nombre: string
  tpda: number
  r: number
  pesado: boolean
  ejes: Eje[]
  factor_camion: number | null
}

export interface Transito {
  n: number
  fd: number
  fc: number
  carriles: number
  pt: number
  sn_lef: number
  unidad_carga: 't' | 'kip'
  vehiculos: Vehiculo[]
}

export interface Periodo {
  nombre: string
  meses: number
  cbr: number | null
  mr: number | null
}

export interface Capa {
  e_psi: number | null
  cbr: number | null
  a: number | null
  m: number
}

export interface Diseno {
  r_pct: number
  etapas: number
  so: number
  p0: number
  pt: number
  fuente_w18: 'calculado' | 'dato'
  w18_dato: number | null
  fuente_mr: 'calculado' | 'dato'
  mr_dato: number | null
  carpeta: Capa
  base: Capa
  subbase: Capa
  paso_sn: number
  unidad: 'cm' | 'pulg'
  paso_espesor: number
  minimos: 'aashto' | 'personalizado' | 'ninguno'
  min_carpeta: number
  min_base: number
  min_subbase: number
  tipo_via?: string | null
  zona?: string | null
  drenaje_calidad?: number | null
  drenaje_saturacion?: number | null
}

export interface Helada {
  pf: number
  dpsi_max: number
  phi: number
}

export interface Clima {
  activo: boolean
  hinchamiento: boolean
  vr: number
  ps: number
  theta: number
  helada: Helada | null
}

export interface Proyecto {
  nombre: string
  autor: string
  ubicacion: string
  descripcion: string
  transito: Transito
  subrasante: { periodos: Periodo[]; dato?: 'cbr' | 'mr' }
  diseno: Diseno
  clima: Clima
}

// ------------------------------------------------------------------ resultado
export interface EjeRes {
  tipo: TipoEje
  carga: number
  unidad: 't' | 'kip'
  carga_kip: number
  lef: number
}

export interface FilaTransito {
  nombre: string
  tpda: number
  r: number
  factor_camion: number
  origen_fc: 'ejes' | 'dato'
  ejes: EjeRes[]
  faltan: string[]
  g: number
  esal1: number
  w: number
  w_bruto: number
}

export interface ResTransito {
  filas: FilaTransito[]
  tpda_total: number
  esal1_total: number
  w18: number
  n: number
  fd: number
  fc: number
  pt_lef: number
  sn_lef: number
  unidad_carga: 't' | 'kip'
  kip_por_t: number
  carriles: number
}

export interface ResSubrasante {
  filas: { nombre: string; meses: number; cbr: number | null; mr: number; origen: string; uf: number; uf_meses: number }[]
  suma_uf: number
  uf_bar: number
  mr_efectivo: number
  mr_promedio: number
}

export interface Material {
  e: number
  a: number
  m?: number
  origen_a: string
  origen_e: string
  cbr?: number | null
}

export interface ResDiseno {
  w18: number
  fuente_w18: string
  log_w18: number
  mr: number
  fuente_mr: string
  r_pct: number
  etapas: number
  r_etapa: number
  zr: number
  so: number
  p0: number
  pt: number
  dpsi: number
  sn_requerido: number
  sn_adoptado: number
  materiales: { carpeta: Material; base: Material; subbase: Material }
  log_w_admisible: number
}

export interface CapaRes {
  capa: string
  a: number
  m: number
  sn_req: number
  d_calc: number
  d: number
  d_pulg: number
  d_cm: number
  sn_aporte: number
  minimo: number
}

export interface ResCapas {
  unidad: 'cm' | 'pulg'
  capas: CapaRes[]
  sn1: number
  sn2: number
  sn3: number
  sn_total: number
  verificaciones: { criterio: string; izq: number; der: number; cumple: boolean }[]
  cumple: boolean
  espesor_total: number
  minimos: number[]
  origen_minimos: string
  w_diseno: number
  dpsi_diseno: number
}

export interface ResClima {
  periodo: number
  w_adm: number
  iteraciones: { t: number; dpsi_sw: number; dpsi_fh: number; dpsi_tr: number; w_adm: number; t_calc: number }[]
  dpsi_sw: number
  dpsi_tr: number
  dpsi_fh: number
  t_objetivo: number
}

export type Modulo = 'transito' | 'subrasante' | 'diseno' | 'clima'

export interface Aviso {
  modulo: Modulo
  texto: string
  nivel: 'error' | 'warn' | 'info'
}

export interface Resultado {
  proyecto?: string
  transito: ResTransito | null
  subrasante: ResSubrasante | null
  diseno: ResDiseno | null
  clima: ResClima | null
  capas: ResCapas | null
  avisos: Aviso[]
  sn_sugerido?: number
  decisiones: { modulo: Modulo; texto: string }[]
  ok: boolean
}
