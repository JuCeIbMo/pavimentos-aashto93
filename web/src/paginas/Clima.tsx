import { useEffect, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import {
  Avisos, CampoNumero, Concepto, Decisiones, Ecuaciones, Encabezado, Interruptor, Kpi, Kpis, Nota, Tabla, Tarjeta, cx, tdNum, th,
} from '../components/ui'
import { api } from '../lib/api'
import { entero, g, num } from '../lib/formato'
import { useApp, useProyecto } from '../lib/store'

const AYUDA = {
  vr: 'Levantamiento vertical potencial (pulg): cuánto podría subir la superficie si la arcilla se hincha por completo.',
  ps: 'Probabilidad de hinchamiento (%): porcentaje del tramo con suelo expansivo.',
  theta: 'Tasa de hinchamiento (0,04–0,20): qué tan rápido ocurre. Depende de la permeabilidad y de las fisuras del suelo.',
  pf: 'Probabilidad de levantamiento por helada (%): porcentaje del tramo afectado.',
  dpsi_max: 'Pérdida máxima de serviciabilidad por helada (figura G.7, según drenaje y profundidad de congelamiento).',
  phi: 'Tasa de levantamiento por helada (mm/día), según el tipo de suelo (figura G.6).',
}

export default function Clima() {
  const p = useProyecto()
  const c = p.clima
  const editar = useApp((s) => s.editar)
  const cl = useApp((s) => s.resultado?.clima)

  return (
    <div className="space-y-6">
      <Encabezado num="6" titulo="Ajuste de la vida útil por clima" sub="Suelos expansivos y heladas: cuánto acortan la vida del pavimento." />

      <Concepto titulo="¿Cómo afecta el clima a la vida útil?">
        <p>El tránsito no es lo único que gasta la serviciabilidad. Una <strong>arcilla expansiva</strong> que se hincha, o una subrasante que
          sufre <strong>levantamiento por congelamiento</strong>, deforman la superficie aunque no pase ningún camión. Esa pérdida
          (ΔPSI<sub>SW</sub> + ΔPSI<sub>FH</sub>) se le <strong>resta</strong> al ΔPSI de diseño, y al tránsito le queda menos margen: el
          pavimento dura menos.</p>
        <p>El procedimiento (AASHTO 93, Parte II, 3.1.4) es iterativo:</p>
        <ol>
          <li>Se supone un período de desempeño t (p. ej. el de diseño).</li>
          <li>Se calcula la pérdida ambiental a esa edad y el ΔPSI que queda para el tránsito.</li>
          <li>Con la ecuación AASHTO se obtiene cuánto tránsito admite la estructura.</li>
          <li>Se busca en qué año se acumula ese tránsito. Si difiere del t supuesto en más de 1 año, se repite.</li>
        </ol>
        <p>El resultado indica <strong>a qué edad hará falta una rehabilitación</strong> (recapado) con el SN elegido.</p>
      </Concepto>

      <Tarjeta>
        <Interruptor activo={c.activo} alCambiar={(v) => editar((p) => { p.clima.activo = v })}>
          <span className="font-medium">Considerar efectos ambientales en el diseño</span>
        </Interruptor>
        <p className="mt-2 text-[13px] text-slate-500">
          {c.activo ? 'Los espesores se diseñan con el tránsito admisible hasta la rehabilitación y el ΔPSI que queda para el tránsito.'
            : 'Activalo si la subrasante es expansiva o susceptible a la helada.'}
        </p>
      </Tarjeta>

      {c.activo && (
        <>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Tarjeta titulo="Hinchamiento (suelos expansivos)"
              acciones={<Interruptor activo={c.hinchamiento} alCambiar={(v) => editar((p) => { p.clima.hinchamiento = v })}>Incluir</Interruptor>}>
              <div className={cx('grid grid-cols-3 gap-4', !c.hinchamiento && 'pointer-events-none opacity-40')}>
                <CampoNumero etiqueta="VR (pulg)" ayuda={AYUDA.vr} valor={c.vr} min={0} max={10} alCambiar={(v) => editar((p) => { p.clima.vr = v ?? 0 })} />
                <CampoNumero etiqueta="PS (%)" ayuda={AYUDA.ps} valor={c.ps} dec={1} min={0} max={100} alCambiar={(v) => editar((p) => { p.clima.ps = v ?? 0 })} />
                <CampoNumero etiqueta="θ" ayuda={AYUDA.theta} valor={c.theta} dec={3} min={0} max={0.3} alCambiar={(v) => editar((p) => { p.clima.theta = v ?? 0 })} />
              </div>
            </Tarjeta>
            <Tarjeta titulo="Levantamiento por helada"
              acciones={<Interruptor activo={c.helada != null} alCambiar={(v) => editar((p) => { p.clima.helada = v ? { pf: 50, dpsi_max: 1, phi: 2 } : null })}>Incluir</Interruptor>}>
              {c.helada ? (
                <div className="grid grid-cols-3 gap-4">
                  <CampoNumero etiqueta="PF (%)" ayuda={AYUDA.pf} valor={c.helada.pf} dec={1} min={0} max={100} alCambiar={(v) => editar((p) => { p.clima.helada!.pf = v ?? 0 })} />
                  <CampoNumero etiqueta="ΔPSI máx" ayuda={AYUDA.dpsi_max} valor={c.helada.dpsi_max} min={0} max={3} alCambiar={(v) => editar((p) => { p.clima.helada!.dpsi_max = v ?? 0 })} />
                  <CampoNumero etiqueta="φ (mm/día)" ayuda={AYUDA.phi} valor={c.helada.phi} dec={1} min={0} max={30} alCambiar={(v) => editar((p) => { p.clima.helada!.phi = v ?? 0 })} />
                </div>
              ) : <p className="text-[13.5px] text-slate-500">No se considera la helada.</p>}
            </Tarjeta>
          </div>

          <Avisos modulo="clima" />

          {cl && (
            <>
              <Kpis>
                <Kpi destacado etiqueta="Período de desempeño" valor={`${num(cl.periodo, 1)} años`} sub={`objetivo: ${g(cl.t_objetivo)} años`} />
                <Kpi etiqueta="ΔPSI ambiental" valor={num(cl.dpsi_sw + cl.dpsi_fh, 3)} sub="hinchamiento + helada" />
                <Kpi etiqueta="ΔPSI para el tránsito" valor={num(cl.dpsi_tr, 3)} sub="ΔPSI TR" />
                <Kpi etiqueta="W admisible" valor={entero(cl.w_adm)} sub="ESAL hasta la rehabilitación" />
              </Kpis>
              <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
                <Tarjeta titulo="Iteraciones" sub="Converge cuando |Δt| < 1 año; se adopta el promedio entre el t supuesto y el calculado." pad={false}>
                  <Tabla>
                    <thead>
                      <tr>
                        <th className={cx(th, 'text-right')}>t supuesto</th>
                        <th className={cx(th, 'text-right')}>ΔPSI SW</th>
                        <th className={cx(th, 'text-right')}>ΔPSI FH</th>
                        <th className={cx(th, 'text-right')}>ΔPSI TR</th>
                        <th className={cx(th, 'text-right')}>W admisible</th>
                        <th className={cx(th, 'text-right')}>t calculado</th>
                        <th className={cx(th, 'text-right')}>|Δt|</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cl.iteraciones.map((it, i) => {
                        const dt = Math.abs(it.t - it.t_calc)
                        return (
                          <tr key={i}>
                            <td className={tdNum}>{num(it.t, 2)}</td>
                            <td className={tdNum}>{num(it.dpsi_sw, 3)}</td>
                            <td className={tdNum}>{num(it.dpsi_fh, 3)}</td>
                            <td className={tdNum}>{num(it.dpsi_tr, 3)}</td>
                            <td className={tdNum}>{entero(it.w_adm)}</td>
                            <td className={tdNum}>{num(it.t_calc, 2)}</td>
                            <td className={cx(tdNum, dt < 1 ? 'text-emerald-600' : 'text-slate-500')}>{num(dt, 2)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </Tabla>
                </Tarjeta>
                <CurvaAmbiental periodo={cl.periodo} objetivo={cl.t_objetivo} />
              </div>
              {cl.periodo < cl.t_objetivo - 0.05 && (
                <Nota tipo="tip">Para alcanzar el período objetivo sin rehabilitación, aumentá el SN (más espesor) o mejorá la subrasante
                  (estabilización, reemplazo del suelo expansivo).</Nota>
              )}
            </>
          )}
        </>
      )}

      <Decisiones modulo="clima" />
      <Ecuaciones claves={['hinchamiento', 'helada', 'periodo']} />
    </div>
  )
}

function CurvaAmbiental({ periodo, objetivo }: { periodo: number; objetivo: number }) {
  const p = useProyecto()
  const [datos, setDatos] = useState<{ t: number; sw: number; fh: number; total: number }[]>([])
  const tmax = Math.max(20, objetivo * 1.5)
  const clave = JSON.stringify(p.clima)
  useEffect(() => { api.curvaClima(p, tmax).then(setDatos) }, [clave, tmax]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <Tarjeta titulo="Pérdida ambiental de serviciabilidad en el tiempo" sub="La línea punteada marca el período de desempeño obtenido.">
      <div className="h-64">
        <ResponsiveContainer>
          <LineChart data={datos} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
            <CartesianGrid stroke="#eef0f3" />
            <XAxis dataKey="t" type="number" domain={[0, tmax]} tickFormatter={(v) => g(v, 0)} tick={{ fontSize: 12, fill: '#64748b' }}
              label={{ value: 'años', position: 'insideBottomRight', offset: -2, fontSize: 12, fill: '#94a3b8' }} />
            <YAxis tick={{ fontSize: 12, fill: '#64748b' }} tickFormatter={(v) => num(v, 2)} />
            <Tooltip formatter={(v) => num(Number(v), 3)} labelFormatter={(v) => `t = ${num(Number(v), 1)} años`}
              contentStyle={{ borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 13 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <ReferenceLine x={periodo} stroke="#64748b" strokeDasharray="4 3" />
            <Line dataKey="sw" name="Hinchamiento" stroke="#94a3b8" dot={false} strokeWidth={2} />
            <Line dataKey="fh" name="Helada" stroke="#f59e0b" dot={false} strokeWidth={2} />
            <Line dataKey="total" name="Total ambiental" stroke="#0f172a" dot={false} strokeWidth={2.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Tarjeta>
  )
}
