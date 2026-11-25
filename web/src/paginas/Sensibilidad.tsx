import { Gauge, Loader2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import {
  CampoNumero, CampoSelector, CampoTexto, Concepto, Encabezado, Nota, Numero, Segmentado, Tabla, Tarjeta, cx, td, tdNum, th,
} from '../components/ui'
import { api, type Barrido, type FilaEscenario, type FilaTornado, type VariableSens } from '../lib/api'
import { auto, entero, g, num } from '../lib/formato'
import { useApp, useProyecto } from '../lib/store'

const tooltipEstilo = { borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 13 }
const eje = { fontSize: 12, fill: '#64748b' }

export default function Sensibilidad() {
  const r = useApp((s) => s.resultado)
  const [tab, setTab] = useState<'curva' | 'tornado' | 'escenarios'>('curva')
  const [vars, setVars] = useState<VariableSens[]>([])
  useEffect(() => { api.variables().then(setVars) }, [])

  return (
    <div className="space-y-6">
      <Encabezado num={<Gauge className="h-5 w-5" />} titulo="Sensibilidad y escenarios" sub="Cómo cambia el diseño cuando cambian los supuestos, y qué variable pesa más." />
      <Concepto titulo="¿Para qué sirve un análisis de sensibilidad?">
        <p>Un diseño no es un número: es la respuesta a un conjunto de supuestos. Esta página muestra <strong>qué pasa si un supuesto
          cambia</strong> y <strong>cuál pesa más</strong>. Cada punto es el diseño completo recalculado (con los mismos mínimos y redondeos).</p>
        <ul>
          <li><strong>Curva:</strong> se mueve una variable en todo su rango. El SN varía de forma continua; el espesor total, en escalones, por el redondeo.</li>
          <li><strong>Tornado:</strong> cada variable se mueve ±X %. Las barras más largas son las variables a las que el diseño es más sensible:
            conviene medirlas mejor (más ensayos de M<sub>R</sub>, mejor conteo de tránsito).</li>
          <li><strong>Escenarios:</strong> alternativas completas lado a lado (otra confiabilidad, mejor drenaje, subrasante mejorada…) para decidir con números.</li>
        </ul>
      </Concepto>

      {!r?.capas ? (
        <Nota>Primero completá los módulos 1, 2 y 4 (o cargá un ejemplo desde Inicio).</Nota>
      ) : (
        <>
          <Segmentado valor={tab} alCambiar={setTab} opciones={[
            { valor: 'curva', etiqueta: 'Curva de una variable' }, { valor: 'tornado', etiqueta: 'Tornado' }, { valor: 'escenarios', etiqueta: 'Escenarios' },
          ]} />
          {tab === 'curva' && <Curva vars={vars} />}
          {tab === 'tornado' && <Tornado vars={vars} />}
          {tab === 'escenarios' && <Escenarios vars={vars} />}
          <p className="text-[12.5px] text-slate-500">
            Proyecto actual: W18 = {entero(r.diseno!.w18)} · MR = {entero(r.diseno!.mr)} psi · SN requerido = {num(r.diseno!.sn_requerido, 3)}
          </p>
        </>
      )}
    </div>
  )
}

function useDebounced<T>(v: T, ms = 300) {
  const [d, setD] = useState(v)
  useEffect(() => { const t = setTimeout(() => setD(v), ms); return () => clearTimeout(t) }, [v, ms])
  return d
}

function Curva({ vars }: { vars: VariableSens[] }) {
  const p = useProyecto()
  const [clave, setClave] = useState('mr')
  const [rango, setRango] = useState<{ desde?: number; hasta?: number }>({})
  const [datos, setDatos] = useState<Barrido | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pedido = useDebounced(JSON.stringify({ p, clave, rango }))
  useEffect(() => {
    setCargando(true)
    api.barrido(p, clave, rango.desde, rango.hasta)
      .then((d) => { setDatos(d); setError(null) }).catch((e) => setError(e.message)).finally(() => setCargando(false))
  }, [pedido]) // eslint-disable-line react-hooks/exhaustive-deps
  const v = vars.find((x) => x.clave === clave)
  const log = clave === 'w18'
  const u = datos?.puntos[0]?.unidad ?? ''

  return (
    <div className="space-y-6">
      <Tarjeta>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-[2fr_1fr_1fr]">
          <CampoSelector etiqueta="Variable" valor={clave} opciones={vars.map((x) => ({ valor: x.clave, etiqueta: `${x.etiqueta} (${x.unidad})` }))}
            alCambiar={(c) => { setClave(c); setRango({}) }} />
          <CampoNumero etiqueta="Desde" valor={rango.desde ?? datos?.desde ?? null} dec={clave === 'w18' || clave === 'mr' ? 0 : 2} alCambiar={(x) => setRango((r) => ({ ...r, desde: x ?? undefined }))} />
          <CampoNumero etiqueta="Hasta" valor={rango.hasta ?? datos?.hasta ?? null} dec={clave === 'w18' || clave === 'mr' ? 0 : 2} alCambiar={(x) => setRango((r) => ({ ...r, hasta: x ?? undefined }))} />
        </div>
        {error && <p className="mt-2 text-[13px] text-red-600">{error}</p>}
      </Tarjeta>
      {datos && (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Tarjeta titulo="SN requerido y espesor total" sub={<>Línea oscura: SN · ámbar: espesor total ({u}) · punteada: valor actual ({auto(datos.x0)}). {cargando && <Loader2 className="inline h-3 w-3 animate-spin" />}</>}>
            <div className="h-72">
              <ResponsiveContainer>
                <ComposedChart data={datos.puntos} margin={{ top: 8, right: 4, left: -8, bottom: 0 }}>
                  <CartesianGrid stroke="#eef0f3" />
                  <XAxis dataKey="x" type="number" scale={log ? 'log' : 'linear'} domain={['dataMin', 'dataMax']} tick={eje} tickFormatter={(x) => auto(x)} />
                  <YAxis yAxisId="sn" tick={eje} domain={['auto', 'auto']} tickFormatter={(x) => num(x, 1)} />
                  <YAxis yAxisId="e" orientation="right" tick={eje} domain={['auto', 'auto']} tickFormatter={(x) => g(x, 1)} />
                  <Tooltip contentStyle={tooltipEstilo} labelFormatter={(x) => `${v?.etiqueta ?? ''} = ${auto(Number(x))}`}
                    formatter={(val, n) => [n === 'SN requerido' ? num(Number(val), 3) : `${num(Number(val), 1)} ${u}`, n]} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <ReferenceLine yAxisId="sn" x={datos.x0} stroke="#94a3b8" strokeDasharray="4 3" />
                  <Line yAxisId="sn" dataKey="sn_requerido" name="SN requerido" stroke="#0f172a" strokeWidth={2.5} dot={false} />
                  <Line yAxisId="e" dataKey="espesor_total" name="Espesor total" stroke="#f59e0b" strokeWidth={2} dot={false} type="stepAfter" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Tarjeta>
          <Tarjeta titulo="Cómo se reparte el espesor" sub="Carpeta, base y subbase a lo largo del rango.">
            <div className="h-72">
              <ResponsiveContainer>
                <AreaChart data={datos.puntos} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                  <CartesianGrid stroke="#eef0f3" />
                  <XAxis dataKey="x" type="number" scale={log ? 'log' : 'linear'} domain={['dataMin', 'dataMax']} tick={eje} tickFormatter={(x) => auto(x)} />
                  <YAxis tick={eje} />
                  <Tooltip contentStyle={tooltipEstilo} labelFormatter={(x) => `${v?.etiqueta ?? ''} = ${auto(Number(x))}`} formatter={(val, n) => [`${num(Number(val), 1)} ${u}`, n]} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Area type="stepAfter" dataKey="d1" name="Carpeta" stackId="1" stroke="#334155" fill="#334155" fillOpacity={0.95} />
                  <Area type="stepAfter" dataKey="d2" name="Base" stackId="1" stroke="#c9a457" fill="#d6b46b" fillOpacity={0.95} />
                  <Area type="stepAfter" dataKey="d3" name="Subbase" stackId="1" stroke="#d8c9a3" fill="#e8dcc0" fillOpacity={0.95} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Tarjeta>
        </div>
      )}
      {v && <Nota tipo="tip">{v.explicacion}</Nota>}
    </div>
  )
}

function Tornado({ vars }: { vars: VariableSens[] }) {
  const p = useProyecto()
  const [variacion, setVariacion] = useState(20)
  const [metrica, setMetrica] = useState<'sn' | 'espesor'>('sn')
  const [filas, setFilas] = useState<FilaTornado[]>([])
  const [cargando, setCargando] = useState(false)
  const pedido = useDebounced(JSON.stringify({ p, variacion, metrica }))
  useEffect(() => {
    setCargando(true)
    api.tornado(p, variacion / 100, metrica).then(setFilas).finally(() => setCargando(false))
  }, [pedido]) // eslint-disable-line react-hooks/exhaustive-deps
  const sn = metrica === 'sn'
  const base = filas[0] ? (sn ? filas[0].sn_base : filas[0].esp_base) : 0
  const datos = filas.map((f) => ({
    etiqueta: f.etiqueta,
    menos: [base, sn ? f.sn_lo : f.esp_lo] as [number, number],
    mas: [base, sn ? f.sn_hi : f.esp_hi] as [number, number],
  }))
  const titulo = sn ? 'SN requerido' : `espesor total (${filas[0]?.unidad ?? ''})`
  const extremos = datos.flatMap((d) => [d.menos[1], d.mas[1], base])
  const lo = Math.min(...extremos), hi = Math.max(...extremos)
  const pad = (hi - lo) * 0.08 || 0.1
  const dominio: [number, number] = [lo - pad, hi + pad]
  const top = filas[0]

  return (
    <div className="space-y-6">
      <Tarjeta>
        <div className="flex flex-wrap items-end gap-8">
          <div className="w-72">
            <div className="mb-1.5 flex justify-between text-[13px] font-medium text-slate-600">Variación de cada parámetro <span className="font-mono">±{variacion} %</span></div>
            <input type="range" min={5} max={50} step={5} value={variacion} onChange={(e) => setVariacion(Number(e.target.value))} className="w-full accent-amber-500" />
          </div>
          <div>
            <div className="mb-1.5 text-[13px] font-medium text-slate-600">Medir el efecto sobre</div>
            <Segmentado valor={metrica} alCambiar={setMetrica} opciones={[{ valor: 'sn', etiqueta: 'SN requerido' }, { valor: 'espesor', etiqueta: 'Espesor total' }]} />
          </div>
          {cargando && <Loader2 className="mb-2 h-4 w-4 animate-spin text-slate-400" />}
        </div>
      </Tarjeta>
      {filas.length > 0 && (
        <Tarjeta titulo={`Tornado: efecto de ±${variacion} % sobre el ${titulo}`} sub="Ordenado de la variable más influyente a la menos. La línea vertical es el valor del proyecto.">
          <div style={{ height: 60 + 52 * filas.length }}>
            <ResponsiveContainer>
              <BarChart data={datos} layout="vertical" margin={{ top: 4, right: 24, left: 24, bottom: 0 }} barCategoryGap={10}>
                <CartesianGrid horizontal={false} stroke="#eef0f3" />
                <XAxis type="number" domain={dominio} allowDataOverflow tick={eje} tickFormatter={(x) => num(x, sn ? 2 : 1)} />
                <YAxis type="category" dataKey="etiqueta" width={230} tick={{ fontSize: 12.5, fill: '#334155' }} />
                <Tooltip contentStyle={tooltipEstilo} formatter={(val, n) => [num((val as number[])[1], sn ? 3 : 1), n]} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine x={base} stroke="#0f172a" />
                <Bar dataKey="menos" name={`−${variacion} %`} fill="#94a3b8" radius={4} />
                <Bar dataKey="mas" name={`+${variacion} %`} fill="#f59e0b" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {top && (
            <Nota tipo="tip">
              La variable más influyente es <strong>{top.etiqueta}</strong>: al variarla ±{variacion} % el {titulo} va de{' '}
              <b className="font-mono">{auto(sn ? top.sn_lo : top.esp_lo)}</b> a <b className="font-mono">{auto(sn ? top.sn_hi : top.esp_hi)}</b>.{' '}
              {vars.find((x) => x.clave === top.clave)?.explicacion}
            </Nota>
          )}
        </Tarjeta>
      )}
      {filas.length > 0 && (
        <Tarjeta pad={false} titulo="Valores">
          <Tabla>
            <thead><tr>
              <th className={th}>Variable</th><th className={cx(th, 'text-right')}>Actual</th>
              <th className={cx(th, 'text-right')}>−{variacion} %</th><th className={cx(th, 'text-right')}>+{variacion} %</th>
              <th className={cx(th, 'text-right')}>SN −</th><th className={cx(th, 'text-right')}>SN +</th>
              <th className={cx(th, 'text-right')}>Espesor −</th><th className={cx(th, 'text-right')}>Espesor +</th>
            </tr></thead>
            <tbody>{filas.map((f) => (
              <tr key={f.clave}>
                <td className={td}>{f.etiqueta}</td><td className={tdNum}>{auto(f.x0)}</td><td className={tdNum}>{auto(f.x_lo)}</td><td className={tdNum}>{auto(f.x_hi)}</td>
                <td className={tdNum}>{num(f.sn_lo, 3)}</td><td className={tdNum}>{num(f.sn_hi, 3)}</td>
                <td className={tdNum}>{num(f.esp_lo, 1)}</td><td className={tdNum}>{num(f.esp_hi, 1)}</td>
              </tr>
            ))}</tbody>
          </Tabla>
        </Tarjeta>
      )}
    </div>
  )
}

interface Esc { nombre: string; cambios: Record<string, number> }

function Escenarios({ vars }: { vars: VariableSens[] }) {
  const p = useProyecto()
  const r = useApp((s) => s.resultado)!
  const actual = useMemo<Record<string, number>>(() => ({
    w18: r.diseno!.w18, mr: r.diseno!.mr, r_pct: p.diseno.r_pct, so: p.diseno.so, pt: p.diseno.pt, m: p.diseno.base.m,
  }), [r, p])
  const [escs, setEscs] = useState<Esc[]>((): Esc[] => [
    { nombre: 'Mayor confiabilidad', cambios: { r_pct: 95 } },
    { nombre: 'Buen drenaje', cambios: { m: 1.2 } },
    { nombre: 'Subrasante mejorada', cambios: { mr: Math.round((r.diseno!.mr * 1.5) / 100) * 100 } },
  ])
  const [filas, setFilas] = useState<FilaEscenario[]>([])
  const pedido = useDebounced(JSON.stringify({ p, escs }))
  useEffect(() => { api.escenarios(p, escs).then(setFilas) }, [pedido]) // eslint-disable-line react-hooks/exhaustive-deps
  const u = filas[0]?.unidad ?? ''
  const dec = (c: string) => (c === 'w18' || c === 'mr' ? 0 : c === 'r_pct' ? 1 : 2)

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {escs.map((e, i) => (
          <Tarjeta key={i}>
            <CampoTexto etiqueta={`Escenario ${i + 1}`} valor={e.nombre} alCambiar={(v) => setEscs((s) => s.map((x, k) => (k === i ? { ...x, nombre: v } : x)))} />
            <div className="mt-3 space-y-2">
              {vars.map((v) => {
                const cambiado = e.cambios[v.clave] != null
                return (
                  <div key={v.clave} className="flex items-center gap-2">
                    <span className={cx('flex-1 text-[12.5px]', cambiado ? 'font-semibold text-acento-700' : 'text-slate-500')}>{v.etiqueta}</span>
                    <CampoNumeroCompacto valor={e.cambios[v.clave] ?? actual[v.clave]} dec={dec(v.clave)} resaltado={cambiado}
                      alCambiar={(x) => setEscs((s) => s.map((y, k) => {
                        if (k !== i) return y
                        const c = { ...y.cambios }
                        if (x == null || Math.abs(x - actual[v.clave]) < 1e-9) delete c[v.clave]; else c[v.clave] = x
                        return { ...y, cambios: c }
                      }))} />
                  </div>
                )
              })}
            </div>
          </Tarjeta>
        ))}
      </div>
      {filas.length > 0 && (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.4fr_1fr]">
          <Tarjeta titulo="Comparación" pad={false}>
            <Tabla>
              <thead><tr>
                <th className={th}>Escenario</th><th className={cx(th, 'text-right')}>W18</th><th className={cx(th, 'text-right')}>MR</th>
                <th className={cx(th, 'text-right')}>R</th><th className={cx(th, 'text-right')}>SN req.</th>
                <th className={cx(th, 'text-right')}>Carpeta</th><th className={cx(th, 'text-right')}>Base</th><th className={cx(th, 'text-right')}>Subbase</th>
                <th className={cx(th, 'text-right')}>Total ({u})</th>
              </tr></thead>
              <tbody>{filas.map((f, i) => {
                const dif = i > 0 && f.espesor_total != null && filas[0].espesor_total != null ? f.espesor_total - filas[0].espesor_total : null
                return (
                  <tr key={i} className={i === 0 ? 'bg-slate-50 font-medium' : ''}>
                    <td className={td}>{f.escenario}</td><td className={tdNum}>{entero(f.w18)}</td><td className={tdNum}>{entero(f.mr)}</td>
                    <td className={tdNum}>{num(f.r_pct, 1)}</td><td className={tdNum}>{num(f.sn_requerido, 3)}</td>
                    <td className={tdNum}>{num(f.d1, 1)}</td><td className={tdNum}>{num(f.d2, 1)}</td><td className={tdNum}>{num(f.d3, 1)}</td>
                    <td className={tdNum}>
                      <b>{num(f.espesor_total, 1)}</b>
                      {dif != null && <span className={cx('ml-1.5 text-[11.5px]', dif > 0 ? 'text-red-600' : dif < 0 ? 'text-emerald-600' : 'text-slate-400')}>{dif > 0 ? '+' : ''}{num(dif, 1)}</span>}
                    </td>
                  </tr>
                )
              })}</tbody>
            </Tabla>
          </Tarjeta>
          <Tarjeta titulo="Espesores por escenario">
            <div className="h-64">
              <ResponsiveContainer>
                <BarChart data={filas.map((f) => ({ n: f.escenario, d1: f.d1, d2: f.d2, d3: f.d3 }))} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#eef0f3" />
                  <XAxis dataKey="n" tick={{ fontSize: 11, fill: '#64748b' }} interval={0} tickFormatter={(x: string) => (x.length > 13 ? x.slice(0, 12) + '…' : x)} />
                  <YAxis tick={eje} reversed />
                  <Tooltip contentStyle={tooltipEstilo} formatter={(val, n) => [`${num(Number(val), 1)} ${u}`, n]} />
                  <Bar dataKey="d1" name="Carpeta" stackId="a" fill="#334155" />
                  <Bar dataKey="d2" name="Base" stackId="a" fill="#d6b46b" />
                  <Bar dataKey="d3" name="Subbase" stackId="a" fill="#e8dcc0" radius={[0, 0, 6, 6]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-[12px] text-slate-500">Las barras se dibujan hacia abajo, como el corte del pavimento.</p>
          </Tarjeta>
        </div>
      )}
    </div>
  )
}

function CampoNumeroCompacto({ valor, dec, alCambiar, resaltado }: { valor: number; dec: number; alCambiar: (v: number | null) => void; resaltado: boolean }) {
  return (
    <div className={cx('w-32 rounded-lg', resaltado && 'ring-2 ring-acento-300')}>
      <Numero compacto valor={valor} dec={dec} alCambiar={alCambiar} />
    </div>
  )
}
