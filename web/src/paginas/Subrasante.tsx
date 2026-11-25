import { Plus, Trash2 } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import {
  Avisos, Ayuda, Barra, Boton, Concepto, Decisiones, Ecuaciones, Encabezado, Kpi, Kpis, Nota, Numero, Tabla, Tarjeta, cx, td, tdNum, th,
} from '../components/ui'
import { entero, g, num } from '../lib/formato'
import { useApp, useProyecto } from '../lib/store'
import type { Periodo } from '../lib/tipos'

const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

export default function Subrasante() {
  const p = useProyecto()
  const editar = useApp((s) => s.editar)
  const sub = useApp((s) => s.resultado?.subrasante)
  const periodos = p.subrasante.periodos
  const suma = periodos.reduce((a, x) => a + (x.meses || 0), 0)
  const ep = (i: number, fn: (x: Periodo) => void) => editar((p) => fn(p.subrasante.periodos[i]))
  const filasRes = sub && sub.filas.length === periodos.length ? sub.filas : null

  return (
    <div className="space-y-6">
      <Encabezado num="02" titulo="Módulo resiliente efectivo de la subrasante"
        sub="Variación estacional de la subrasante, daño relativo y MR de diseño." />

      <Concepto titulo="¿Por qué un MR «efectivo» y no el promedio?">
        <p>La subrasante no tiene la misma rigidez todo el año: en épocas de lluvia o deshielo se <strong>ablanda</strong> (M<sub>R</sub> bajo)
          y en épocas secas o congelada se <strong>rigidiza</strong> (M<sub>R</sub> alto).</p>
        <p>No alcanza con promediar los M<sub>R</sub>, porque el daño <strong>no es lineal</strong>: un mes débil daña mucho más de lo que un
          mes rígido «compensa». AASHTO calcula el <strong>daño relativo u<sub>f</sub></strong> de cada período, lo promedia ponderando
          por su duración y busca el M<sub>R</sub> constante que produciría ese mismo daño. Ese es el <strong>M<sub>R</sub> efectivo</strong>,
          siempre menor que el promedio aritmético.</p>
        <p>Si solo tenés CBR, el programa estima M<sub>R</sub> con las correlaciones de la guía. Si tenés ensayos triaxiales
          (AASHTO T-307), cargá el M<sub>R</sub> directamente.</p>
      </Concepto>

      <Tarjeta titulo="Variación estacional" pad={false}
        sub="Un renglón por período (mes, quincena o estación). Si cargás MR directo, tiene prioridad sobre el CBR."
        acciones={
          <div className={cx('rounded-lg px-3 py-1.5 font-mono text-[13px]', Math.abs(suma - 12) < 1e-6 ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700')}>
            {g(suma, 2)} / 12 meses
          </div>
        }>
        <Tabla>
          <thead>
            <tr>
              <th className={th}>Período</th>
              <th className={cx(th, 'text-right')}>Duración<br /><span className="font-normal normal-case">meses</span></th>
              <th className={cx(th, 'text-right')}>
                <span className="inline-flex items-center gap-1">CBR <Ayuda texto="MR = 1500·CBR si CBR < 7,2 %; si no, MR = 3000·CBR^0,65 (correlaciones de la guía; válidas hasta CBR 20 %)." /></span>
                <br /><span className="font-normal normal-case">%</span>
              </th>
              <th className={cx(th, 'text-right')}>MR directo<br /><span className="font-normal normal-case">psi (opcional)</span></th>
              <th className={cx(th, 'border-l border-slate-200 text-right')}>MR usado<br /><span className="font-normal normal-case">psi</span></th>
              <th className={cx(th, 'text-right')}>u<sub>f</sub></th>
              <th className={cx(th, 'w-52')}>Parte del daño anual</th>
              <th className={cx(th, 'w-10')} />
            </tr>
          </thead>
          <tbody>
            {periodos.map((x, i) => {
              const f = filasRes?.[i]
              return (
                <tr key={i} className="group hover:bg-slate-50/50">
                  <td className={cx(td, 'px-2')}>
                    <input value={x.nombre} onChange={(e) => ep(i, (y) => { y.nombre = e.target.value })}
                      className="h-8 w-full min-w-32 rounded-md border border-transparent bg-transparent px-2 text-[13.5px] font-medium text-slate-800 hover:border-slate-200 focus:border-acento-500 focus:bg-white focus:outline-none" />
                  </td>
                  <td className={cx(td, 'px-2')}><Numero compacto valor={x.meses} dec={1} className="ml-auto w-20" alCambiar={(v) => ep(i, (y) => { y.meses = v ?? 0 })} /></td>
                  <td className={cx(td, 'px-2')}><Numero compacto vacio valor={x.cbr} dec={2} placeholder="—" className="ml-auto w-20" alCambiar={(v) => ep(i, (y) => { y.cbr = v })} /></td>
                  <td className={cx(td, 'px-2')}><Numero compacto vacio valor={x.mr} dec={0} placeholder="—" className="ml-auto w-28" alCambiar={(v) => ep(i, (y) => { y.mr = v })} /></td>
                  <td className={cx(tdNum, 'border-l border-slate-100')}>{f ? entero(f.mr) : '—'}<div className="text-[10.5px] font-sans text-slate-400">{f?.origen}</div></td>
                  <td className={tdNum}>{f ? num(f.uf, 4) : '—'}</td>
                  <td className={td}>{f && sub ? <Barra valor={(100 * f.uf_meses) / sub.suma_uf} /> : null}</td>
                  <td className={cx(td, 'px-1')}>
                    <button title="Borrar período" onClick={() => editar((p) => { p.subrasante.periodos.splice(i, 1) })}
                      className="grid h-7 w-7 place-items-center rounded-md text-slate-400 opacity-0 hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"><Trash2 className="h-3.5 w-3.5" /></button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </Tabla>
        <div className="flex flex-wrap gap-2 border-t border-slate-100 px-5 py-3">
          <Boton tamano="sm" icono={<Plus className="h-3.5 w-3.5" />}
            onClick={() => editar((p) => { p.subrasante.periodos.push({ nombre: `Período ${p.subrasante.periodos.length + 1}`, meses: 1, cbr: null, mr: null }) })}>
            Agregar período
          </Boton>
          <Boton tamano="sm" variante="fantasma"
            onClick={() => editar((p) => { p.subrasante.periodos = MESES.map((m) => ({ nombre: m, meses: 1, cbr: null, mr: null })) })}>
            Armar los 12 meses
          </Boton>
          <Boton tamano="sm" variante="fantasma"
            onClick={() => editar((p) => { p.subrasante.periodos = ['Verano', 'Otoño', 'Invierno', 'Primavera'].map((m) => ({ nombre: m, meses: 3, cbr: null, mr: null })) })}>
            Armar 4 estaciones
          </Boton>
        </div>
      </Tarjeta>

      <Avisos modulo="subrasante" />

      {sub && (
        <>
          <Kpis>
            <Kpi destacado etiqueta="MR efectivo" valor={`${entero(sub.mr_efectivo)} psi`} sub={`≈ ${entero(sub.mr_efectivo / 14.2233)} kg/cm²`} />
            <Kpi etiqueta="Daño relativo promedio ūf" valor={num(sub.uf_bar, 4)} sub="ponderado por duración" />
            <Kpi etiqueta="Promedio aritmético de MR" valor={`${entero(sub.mr_promedio)} psi`} sub="no se usa: sobreestima el soporte" />
            <Kpi etiqueta="Diferencia" valor={`${num((100 * (sub.mr_promedio - sub.mr_efectivo)) / sub.mr_promedio, 1)} %`} sub="el efectivo es menor que el promedio" />
          </Kpis>

          <Tarjeta titulo="¿Qué período daña más?" sub="Porcentaje del daño anual que produce cada período (uf × meses).">
            <div className="h-64">
              <ResponsiveContainer>
                <BarChart data={sub.filas.map((f) => ({ nombre: f.nombre, danio: (100 * f.uf_meses) / sub.suma_uf, mr: f.mr }))}
                  margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#eef0f3" />
                  <XAxis dataKey="nombre" tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }} interval={0} />
                  <YAxis tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} unit=" %" />
                  <Tooltip cursor={{ fill: '#f8fafc' }} formatter={(v) => [`${num(Number(v), 1)} %`, 'Daño anual']}
                    contentStyle={{ borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 13 }} />
                  <Bar dataKey="danio" radius={[6, 6, 0, 0]}>
                    {sub.filas.map((f, i) => {
                      const max = Math.max(...sub.filas.map((x) => x.uf_meses))
                      return <Cell key={i} fill={f.uf_meses === max ? '#f59e0b' : '#cbd5e1'} />
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            {(() => {
              const peor = sub.filas.reduce((a, b) => (b.uf_meses > a.uf_meses ? b : a))
              return (
                <Nota tipo="tip">
                  «{peor.nombre}» concentra el <strong>{num((100 * peor.uf_meses) / sub.suma_uf, 0)} %</strong> del daño anual con
                  el {num((100 * peor.meses) / 12, 0)} % del tiempo: por eso drenar bien la subrasante rinde tanto.
                </Nota>
              )
            })()}
          </Tarjeta>
        </>
      )}

      <Decisiones modulo="subrasante" />
      <Ecuaciones claves={['mr_cbr', 'danio', 'mr_ef']} />
    </div>
  )
}
