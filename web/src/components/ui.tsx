import katex from 'katex'
import { AlertTriangle, ChevronDown, CircleHelp, Info, Lightbulb, OctagonAlert, Sigma } from 'lucide-react'
import { useEffect, useId, useMemo, useState, type ReactNode } from 'react'
import { leerNumero, num, paraEditar } from '../lib/formato'
import { useApp } from '../lib/store'
import type { Modulo } from '../lib/tipos'

export function cx(...c: (string | false | null | undefined)[]) {
  return c.filter(Boolean).join(' ')
}

// ------------------------------------------------------------------ estructura de página
export function Encabezado({ num: n, titulo, sub }: { num: string; titulo: string; sub: string }) {
  return (
    <header className="mb-6 flex items-start gap-4">
      <div className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-slate-900 font-mono text-lg font-semibold text-acento-400 shadow-sm">
        {n}
      </div>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{titulo}</h1>
        <p className="mt-0.5 text-[15px] text-slate-500">{sub}</p>
      </div>
    </header>
  )
}

export function Tarjeta({ titulo, sub, children, acciones, className, pad = true }: {
  titulo?: ReactNode; sub?: ReactNode; children: ReactNode; acciones?: ReactNode; className?: string; pad?: boolean
}) {
  return (
    <section className={cx('rounded-2xl border border-slate-200 bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]', className)}>
      {(titulo || acciones) && (
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 px-5 py-3.5">
          <div>
            {titulo && <h2 className="text-[15px] font-semibold text-slate-900">{titulo}</h2>}
            {sub && <p className="mt-0.5 text-[13px] text-slate-500">{sub}</p>}
          </div>
          {acciones}
        </div>
      )}
      <div className={pad ? 'p-5' : ''}>{children}</div>
    </section>
  )
}

export function Kpi({ etiqueta, valor, sub, destacado }: { etiqueta: ReactNode; valor: ReactNode; sub?: ReactNode; destacado?: boolean }) {
  return (
    <div className={cx('rounded-xl border px-4 py-3', destacado ? 'border-acento-200 bg-acento-50' : 'border-slate-200 bg-white')}>
      <div className="text-[12px] font-medium uppercase tracking-wide text-slate-500">{etiqueta}</div>
      <div className={cx('num mt-1 font-mono text-[22px] font-semibold leading-tight', destacado ? 'text-acento-700' : 'text-slate-900')}>{valor}</div>
      {sub && <div className="mt-0.5 text-[12.5px] text-slate-500">{sub}</div>}
    </div>
  )
}

export function Kpis({ children }: { children: ReactNode }) {
  return <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{children}</div>
}

// ------------------------------------------------------------------ campos
export function Ayuda({ texto }: { texto: ReactNode }) {
  return (
    <span className="group relative inline-flex align-middle">
      <CircleHelp className="h-3.5 w-3.5 cursor-help text-slate-400 hover:text-slate-600" />
      <span className="pointer-events-none absolute bottom-full left-1/2 z-30 mb-2 w-72 -translate-x-1/2 rounded-lg bg-slate-900 px-3 py-2 text-[12.5px] font-normal normal-case leading-snug tracking-normal text-slate-100 opacity-0 shadow-lg transition group-hover:opacity-100">
        {texto}
      </span>
    </span>
  )
}

export function Etiqueta({ children, ayuda, htmlFor }: { children: ReactNode; ayuda?: ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 flex items-center gap-1.5 text-[13px] font-medium text-slate-600">
      {children}
      {ayuda && <Ayuda texto={ayuda} />}
    </label>
  )
}

const claseInput =
  'h-9 w-full rounded-lg border border-slate-300 bg-white px-3 text-[14px] text-slate-900 outline-none transition placeholder:text-slate-300 hover:border-slate-400 focus:border-acento-500 focus:ring-3 focus:ring-acento-500/15'

interface PropsNumero {
  valor: number | null
  alCambiar: (v: number | null) => void
  dec?: number
  min?: number
  max?: number
  sufijo?: string
  vacio?: boolean
  placeholder?: string
  className?: string
  compacto?: boolean
  alinear?: 'left' | 'right'
  id?: string
}

/** Campo numérico que acepta coma o punto decimal y muestra el número con formato español. */
export function Numero({ valor, alCambiar, dec = 2, min, max, sufijo, vacio, placeholder, className, compacto, alinear = 'right', id }: PropsNumero) {
  const [texto, setTexto] = useState<string | null>(null)
  const fueraDeRango = valor != null && ((min != null && valor < min) || (max != null && valor > max))
  const mostrado = texto ?? (valor == null ? '' : num(valor, dec))
  return (
    <div className={cx('relative', className)}>
      <input
        id={id}
        inputMode="decimal"
        className={cx(claseInput, 'num font-mono', compacto && 'h-8 px-2 text-[13px]', alinear === 'right' ? 'text-right' : 'text-left',
          sufijo && 'pr-11', fueraDeRango && 'border-red-400 focus:border-red-500 focus:ring-red-500/15')}
        value={mostrado}
        placeholder={placeholder}
        onFocus={(e) => { setTexto(paraEditar(valor)); requestAnimationFrame(() => e.target.select()) }}
        onChange={(e) => {
          setTexto(e.target.value)
          const v = leerNumero(e.target.value)
          if (v !== null) alCambiar(v)
          else if (e.target.value.trim() === '' && vacio) alCambiar(null)
        }}
        onBlur={() => setTexto(null)}
      />
      {sufijo && <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-[12px] text-slate-400">{sufijo}</span>}
    </div>
  )
}

export function CampoNumero({ etiqueta, ayuda, ...p }: PropsNumero & { etiqueta: ReactNode; ayuda?: ReactNode }) {
  const id = useId()
  return (
    <div>
      <Etiqueta ayuda={ayuda} htmlFor={id}>{etiqueta}</Etiqueta>
      <Numero id={id} {...p} />
    </div>
  )
}

export function CampoTexto({ etiqueta, valor, alCambiar, placeholder, area }: {
  etiqueta: ReactNode; valor: string; alCambiar: (v: string) => void; placeholder?: string; area?: boolean
}) {
  const id = useId()
  return (
    <div>
      <Etiqueta htmlFor={id}>{etiqueta}</Etiqueta>
      {area ? (
        <textarea id={id} className={cx(claseInput, 'h-20 py-2')} value={valor} placeholder={placeholder} onChange={(e) => alCambiar(e.target.value)} />
      ) : (
        <input id={id} className={claseInput} value={valor} placeholder={placeholder} onChange={(e) => alCambiar(e.target.value)} />
      )}
    </div>
  )
}

export function Selector<T extends string | number>({ valor, opciones, alCambiar, compacto, className, placeholder, id }: {
  valor: T | null; opciones: { valor: T; etiqueta: string }[]; alCambiar: (v: T) => void; compacto?: boolean
  className?: string; placeholder?: string; id?: string
}) {
  return (
    <div className={cx('relative', className)}>
      <select
        id={id}
        className={cx(claseInput, 'cursor-pointer appearance-none pr-8', compacto && 'h-8 px-2 pr-7 text-[13px]', valor == null && 'text-slate-400')}
        value={valor == null ? '' : String(valor)}
        onChange={(e) => {
          const o = opciones.find((x) => String(x.valor) === e.target.value)
          if (o) alCambiar(o.valor)
        }}
      >
        {valor == null && <option value="">{placeholder ?? '—'}</option>}
        {opciones.map((o) => <option key={String(o.valor)} value={String(o.valor)}>{o.etiqueta}</option>)}
      </select>
      <ChevronDown className={cx('pointer-events-none absolute top-1/2 -translate-y-1/2 text-slate-400', compacto ? 'right-2 h-3.5 w-3.5' : 'right-2.5 h-4 w-4')} />
    </div>
  )
}

export function CampoSelector<T extends string | number>({ etiqueta, ayuda, ...p }: {
  etiqueta: ReactNode; ayuda?: ReactNode; valor: T | null; opciones: { valor: T; etiqueta: string }[]; alCambiar: (v: T) => void
}) {
  const id = useId()
  return (
    <div>
      <Etiqueta ayuda={ayuda} htmlFor={id}>{etiqueta}</Etiqueta>
      <Selector id={id} {...p} />
    </div>
  )
}

/** Botones segmentados (para elegir entre 2–4 opciones a la vista). */
export function Segmentado<T extends string | number>({ valor, opciones, alCambiar }: {
  valor: T; opciones: { valor: T; etiqueta: ReactNode }[]; alCambiar: (v: T) => void
}) {
  return (
    <div className="inline-flex rounded-lg bg-slate-100 p-0.5">
      {opciones.map((o) => (
        <button
          key={String(o.valor)}
          type="button"
          onClick={() => alCambiar(o.valor)}
          className={cx('rounded-md px-3 py-1.5 text-[13px] font-medium transition',
            o.valor === valor ? 'bg-white text-slate-900 shadow-sm ring-1 ring-slate-200' : 'text-slate-500 hover:text-slate-800')}
        >
          {o.etiqueta}
        </button>
      ))}
    </div>
  )
}

export function Interruptor({ activo, alCambiar, children }: { activo: boolean; alCambiar: (v: boolean) => void; children: ReactNode }) {
  return (
    <button type="button" onClick={() => alCambiar(!activo)} className="group inline-flex items-center gap-2.5 text-[14px] text-slate-700">
      <span className={cx('relative h-5 w-9 rounded-full transition', activo ? 'bg-acento-500' : 'bg-slate-300')}>
        <span className={cx('absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all', activo ? 'left-[18px]' : 'left-0.5')} />
      </span>
      {children}
    </button>
  )
}

export function Boton({ children, onClick, variante = 'secundario', icono, disabled, className, title, tamano = 'md' }: {
  children?: ReactNode; onClick?: () => void; variante?: 'primario' | 'secundario' | 'fantasma' | 'oscuro'
  icono?: ReactNode; disabled?: boolean; className?: string; title?: string; tamano?: 'sm' | 'md'
}) {
  const v = {
    primario: 'bg-acento-500 text-slate-950 hover:bg-acento-400 shadow-sm',
    secundario: 'bg-white text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50 hover:ring-slate-400',
    fantasma: 'text-slate-500 hover:bg-slate-100 hover:text-slate-800',
    oscuro: 'bg-slate-900 text-white hover:bg-slate-800',
  }[variante]
  return (
    <button type="button" title={title} disabled={disabled} onClick={onClick}
      className={cx('inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition disabled:cursor-not-allowed disabled:opacity-40',
        tamano === 'sm' ? 'h-8 px-2.5 text-[13px]' : 'h-9 px-3.5 text-[14px]', v, className)}>
      {icono}
      {children}
    </button>
  )
}

// ------------------------------------------------------------------ didáctica
export function Concepto({ titulo, children, abierto = false }: { titulo: string; children: ReactNode; abierto?: boolean }) {
  const [a, setA] = useState(abierto)
  return (
    <div className="mb-6 overflow-hidden rounded-2xl border border-acento-200/70 bg-gradient-to-br from-acento-50 to-white">
      <button type="button" onClick={() => setA(!a)} className="flex w-full items-center gap-3 px-5 py-3.5 text-left">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-acento-100 text-acento-700"><Lightbulb className="h-4 w-4" /></span>
        <span className="flex-1 text-[15px] font-semibold text-slate-800">{titulo}</span>
        <span className="text-[12.5px] text-acento-700">{a ? 'Ocultar' : 'Ver la explicación'}</span>
        <ChevronDown className={cx('h-4 w-4 text-acento-700 transition', a && 'rotate-180')} />
      </button>
      {a && <div className="prosa border-t border-acento-200/60 px-5 py-4 text-[14.5px] leading-relaxed text-slate-700">{children}</div>}
    </div>
  )
}

export function Avisos({ modulo }: { modulo: Modulo }) {
  const res = useApp((s) => s.resultado)
  const avisos = (res?.avisos ?? []).filter((a) => a.modulo === modulo)
  if (!avisos.length) return null
  return (
    <div className="space-y-2">
      {avisos.map((a, i) => (
        <div key={i} className={cx('flex items-start gap-2.5 rounded-xl border px-4 py-2.5 text-[14px]',
          a.nivel === 'error' ? 'border-red-200 bg-red-50 text-red-800' : 'border-amber-200 bg-amber-50 text-amber-900')}>
          {a.nivel === 'error' ? <OctagonAlert className="mt-0.5 h-4 w-4 shrink-0" /> : <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />}
          <span>{a.texto}</span>
        </div>
      ))}
    </div>
  )
}

export function Decisiones({ modulo }: { modulo: Modulo }) {
  const res = useApp((s) => s.resultado)
  const ds = (res?.decisiones ?? []).filter((d) => d.modulo === modulo)
  if (!ds.length) return null
  return (
    <Tarjeta titulo="Decisiones de diseño" sub="Criterios que aplicó el programa (quedan registrados en la memoria PDF).">
      <ul className="space-y-2">
        {ds.map((d, i) => (
          <li key={i} className="flex gap-2.5 text-[14px] text-slate-700">
            <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-acento-500" />
            {d.texto}
          </li>
        ))}
      </ul>
    </Tarjeta>
  )
}

export function Nota({ children, tipo = 'info' }: { children: ReactNode; tipo?: 'info' | 'tip' }) {
  return (
    <div className={cx('flex items-start gap-2.5 rounded-xl px-4 py-2.5 text-[13.5px]',
      tipo === 'tip' ? 'bg-acento-50 text-slate-700' : 'bg-slate-100 text-slate-600')}>
      {tipo === 'tip' ? <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-acento-600" /> : <Info className="mt-0.5 h-4 w-4 shrink-0" />}
      <div>{children}</div>
    </div>
  )
}

export function Latex({ tex, bloque = true }: { tex: string; bloque?: boolean }) {
  const html = useMemo(() => katex.renderToString(tex, { displayMode: bloque, throwOnError: false }), [tex, bloque])
  return <span dangerouslySetInnerHTML={{ __html: html }} />
}

/** Bloque desplegable con las ecuaciones del módulo (texto desde /api/referencias). */
export function Ecuaciones({ claves, children }: { claves: string[]; children?: ReactNode }) {
  const [a, setA] = useState(false)
  const ecs = useEcuaciones()
  return (
    <div className="rounded-2xl border border-slate-200 bg-white">
      <button type="button" onClick={() => setA(!a)} className="flex w-full items-center gap-3 px-5 py-3.5 text-left">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-slate-600"><Sigma className="h-4 w-4" /></span>
        <span className="flex-1 text-[15px] font-semibold text-slate-800">Procedimiento y ecuaciones</span>
        <ChevronDown className={cx('h-4 w-4 text-slate-500 transition', a && 'rotate-180')} />
      </button>
      {a && (
        <div className="space-y-4 border-t border-slate-100 px-5 py-4">
          {claves.map((c) => ecs?.[c] && (
            <div key={c} className="rounded-xl bg-slate-50 px-4 py-3">
              <Latex tex={ecs[c].latex} />
              <p className="mt-1 text-[13px] text-slate-600">{ecs[c].explica}</p>
              <p className="mt-0.5 text-[12px] text-slate-400">Fuente: {ecs[c].fuente}</p>
            </div>
          ))}
          {children}
        </div>
      )}
    </div>
  )
}

// cache simple de ecuaciones
let cacheEcs: Record<string, { latex: string; fuente: string; explica: string }> | null = null
export function useEcuaciones() {
  const [e, setE] = useState(cacheEcs)
  useEffect(() => {
    if (!cacheEcs) fetch('/api/referencias').then((r) => r.json()).then((d) => { cacheEcs = d.ecuaciones; setE(cacheEcs) })
  }, [])
  return e
}

// ------------------------------------------------------------------ tablas
export function Tabla({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cx('overflow-x-auto', className)}>
      <table className="w-full border-collapse text-[13.5px]">{children}</table>
    </div>
  )
}
export const th = 'border-b border-slate-200 bg-slate-50 px-3 py-2 text-left text-[12px] font-semibold uppercase tracking-wide text-slate-500'
export const td = 'border-b border-slate-100 px-3 py-2 text-slate-700'
export const tdNum = 'border-b border-slate-100 px-3 py-2 text-right font-mono num text-slate-800'

export function Barra({ valor, max = 100 }: { valor: number; max?: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-acento-500" style={{ width: `${Math.min(100, (100 * valor) / max)}%` }} />
      </div>
      <span className="num w-12 text-right font-mono text-[12.5px] text-slate-600">{num(valor, 1)} %</span>
    </div>
  )
}
