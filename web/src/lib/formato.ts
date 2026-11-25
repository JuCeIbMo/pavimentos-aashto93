// Formato numérico en español: miles con punto, decimales con coma (igual que pavimentos/formato.py).

export function num(x: number | null | undefined, dec = 2): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '—'
  const neg = x < 0
  const [ent, frac] = Math.abs(x).toFixed(dec).split('.')
  const miles = ent.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return (neg ? '−' : '') + miles + (frac ? ',' + frac : '')
}

export const entero = (x: number | null | undefined) => num(x, 0)
export const pct = (x: number | null | undefined, dec = 1) => (x == null ? '—' : `${num(x, dec)} %`)

/** Decimales razonables según la magnitud. */
export function auto(x: number | null | undefined): string {
  if (x == null) return '—'
  const a = Math.abs(x)
  if (a >= 1000) return num(x, 0)
  if (a >= 100) return num(x, 1)
  if (a >= 1) return num(x, 2)
  if (a === 0) return '0'
  return num(x, 4)
}

/** Número corto sin ceros sobrantes. */
export function g(x: number | null | undefined, dec = 3): string {
  const s = num(x, dec)
  return s.includes(',') ? s.replace(/0+$/, '').replace(/,$/, '') : s
}

/** Interpreta texto escrito por el usuario: acepta coma o punto decimal. */
export function leerNumero(s: string): number | null {
  const t = s.trim().replace(/\s/g, '').replace('−', '-')
  if (!t) return null
  let n: string
  if (t.includes(',')) n = t.replace(/\./g, '').replace(',', '.')
  else n = t
  const v = Number(n)
  return Number.isFinite(v) ? v : null
}

/** Texto para editar un número (coma decimal, sin separador de miles). */
export function paraEditar(x: number | null | undefined, maxDec = 6): string {
  if (x == null) return ''
  const s = Number(x.toFixed(maxDec)).toString()
  return s.replace('.', ',')
}
