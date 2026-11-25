import { ArrowDownToLine, CircleAlert, RotateCcw } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import {
  Avisos, Ayuda, Barra, Boton, Concepto, Decisiones, Ecuaciones, Encabezado, Kpi, Kpis, Nota, Numero, Segmentado, Tabla, Tarjeta, cx, td, tdNum, th,
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
  const ep = (i: number, fn: (x: Periodo) => void) => editar((p) => fn(p.subrasante.periodos[i]))
  const filasRes = sub && sub.filas.length === periodos.length ? sub.filas : null
  const porMes = periodos.length === 12 && periodos.every((x) => x.meses === 1)
  const vacio = (x: Periodo) => x.cbr == null && x.mr == null
  const faltan = periodos.filter(vacio).length
  const dato: 'cbr' | 'mr' = p.subrasante.dato ?? (periodos.some((x) => x.mr != null) ? 'mr' : 'cbr')
  const cambiarDato = (nuevo: 'cbr' | 'mr') => {
    if (nuevo === dato) return
    const conValores = periodos.some((x) => (dato === 'cbr' ? x.cbr : x.mr) != null)
    if (conValores && !window.confirm(`Al pasar a ${nuevo === 'cbr' ? 'CBR' : 'M_R'} se borran los valores cargados de ${dato === 'cbr' ? 'CBR' : 'M_R'}. ¿Seguir?`)) return
    editar((p) => {
      p.subrasante.dato = nuevo
      p.subrasante.periodos.forEach((x) => { x.cbr = null; x.mr = null })
    })
  }
  const doceMeses = () => editar((p) => { p.subrasante.periodos = MESES.map((m) => ({ nombre: m, meses: 1, cbr: null, mr: null })) })

  return (
    <div className="space-y-6">
      <Encabezado num="2" titulo="Módulo resiliente efectivo de la subrasante"
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

      {!porMes && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-[13.5px] text-sky-900">
          <span className="flex-1">Este proyecto trae la variación estacional en {periodos.length} períodos agrupados
            ({periodos.map((x) => `${x.nombre}: ${g(x.meses)} mes${x.meses === 1 ? '' : 'es'}`).join(' · ')}). Se calcula igual,
            pero para editarla hay que pasar a los 12 meses.</span>
          <Boton tamano="sm" icono={<RotateCcw className="h-3.5 w-3.5" />} onClick={doceMeses}>Empezar con los 12 meses vacíos</Boton>
        </div>
      )}

      {porMes && (
        <Tarjeta titulo="Variación estacional" pad={false}
          sub="Un renglón por mes. Elegí arriba qué dato te da el enunciado; con ⤓ copiás el valor al mes siguiente."
          acciones={
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 text-[13px] text-slate-500">
                Dato de cada mes
                <Segmentado valor={dato} alCambiar={cambiarDato}
                  opciones={[{ valor: 'cbr', etiqueta: 'CBR (%)' }, { valor: 'mr', etiqueta: 'M_R (psi)' }]} />
                <Ayuda texto="CBR: el caso usual; el programa calcula M_R con las correlaciones AASHTO. M_R: si el enunciado o un ensayo triaxial ya da el módulo resiliente." />
              </div>
              <div className={cx('rounded-lg px-3 py-1.5 text-[13px] font-medium', faltan ? 'bg-amber-50 text-amber-800' : 'bg-emerald-50 text-emerald-700')}>
                {faltan ? `Faltan ${faltan} de 12 meses` : '12 de 12 meses cargados'}
              </div>
            </div>
          }>
          <Tabla>
            <thead>
              <tr>
                <th className={th}>Mes</th>
                <th className={cx(th, 'text-right')}>
                  {dato === 'cbr'
                    ? <><span className="inline-flex items-center gap-1">CBR <Ayuda texto="M_R = 1500·CBR si CBR < 7,2 %; si no, M_R = 3000·CBR^0,65 (correlaciones de la guía; válidas hasta CBR 20 %)." /></span><br /><span className="font-normal normal-case">%</span></>
                    : <>M_R<br /><span className="font-normal normal-case">psi</span></>}
                </th>
                <th className={cx(th, 'w-10')} />
                <th className={cx(th, 'border-l border-slate-200 text-right')}>M_R usado<br /><span className="font-normal normal-case">psi</span></th>
                <th className={cx(th, 'text-right')}>u<sub>f</sub></th>
                <th className={cx(th, 'w-52')}>Parte del daño anual</th>
              </tr>
            </thead>
            <tbody>
              {periodos.map((x, i) => {
                const f = filasRes?.[i]
                const falta = vacio(x)
                return (
                  <tr key={i} className={cx('group', falta ? 'bg-amber-50/60' : 'hover:bg-slate-50/50')}>
                    <td className={cx(td, 'font-medium text-slate-800')}>
                      <span className="inline-flex items-center gap-1.5">{x.nombre}{falta && <CircleAlert className="h-3.5 w-3.5 text-amber-500" />}</span>
                    </td>
                    <td className={cx(td, 'px-2')}>
                      {dato === 'cbr'
                        ? <Numero compacto vacio valor={x.cbr} dec={2} placeholder="—" className={cx('ml-auto w-24', falta && 'rounded-lg ring-2 ring-amber-300')} alCambiar={(v) => ep(i, (y) => { y.cbr = v; y.mr = null })} />
                        : <Numero compacto vacio valor={x.mr} dec={0} placeholder="—" className={cx('ml-auto w-28', falta && 'rounded-lg ring-2 ring-amber-300')} alCambiar={(v) => ep(i, (y) => { y.mr = v; y.cbr = null })} />}
                    </td>
                    <td className={cx(td, 'px-1')}>
                      {i < 11 && !falta && (
                        <button title={`Copiar a ${periodos[i + 1].nombre}`}
                          onClick={() => editar((p) => { const a = p.subrasante.periodos[i], b = p.subrasante.periodos[i + 1]; b.cbr = a.cbr; b.mr = a.mr })}
                          className="grid h-7 w-7 place-items-center rounded-md text-slate-400 hover:bg-acento-50 hover:text-acento-700"><ArrowDownToLine className="h-3.5 w-3.5" /></button>
                      )}
                    </td>
                    <td className={cx(tdNum, 'border-l border-slate-100')}>{f ? entero(f.mr) : '—'}<div className="text-[10.5px] font-sans text-slate-400">{f?.origen}</div></td>
                    <td className={tdNum}>{f ? num(f.uf, 4) : '—'}</td>
                    <td className={td}>{f && sub ? <Barra valor={(100 * f.uf_meses) / sub.suma_uf} /> : null}</td>
                  </tr>
                )
              })}
            </tbody>
          </Tabla>
          <div className="flex justify-end border-t border-slate-100 px-5 py-2.5">
            <Boton tamano="sm" variante="fantasma" icono={<RotateCcw className="h-3.5 w-3.5" />} onClick={doceMeses}>Vaciar los 12 meses</Boton>
          </div>
        </Tarjeta>
      )}

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
                <BarChart data={sub.filas.map((f) => ({ nombre: porMes ? f.nombre.slice(0, 3) : f.nombre, danio: (100 * f.uf_meses) / sub.suma_uf, mr: f.mr }))}
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
                  {peor.nombre} concentra el <strong>{num((100 * peor.uf_meses) / sub.suma_uf, 0)} %</strong> del daño anual con
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
