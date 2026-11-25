import { CheckCircle2, ChevronDown, FileDown, Info, Loader2, ShieldCheck, Upload, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Boton, Concepto, Encabezado, Kpi, Kpis, Tabla, cx, td, tdNum, th } from '../components/ui'
import { api, descargar, type Validacion as V } from '../lib/api'
import { auto, num } from '../lib/formato'
import { useApp } from '../lib/store'

export default function Validacion() {
  const [datos, setDatos] = useState<V[] | null>(null)
  useEffect(() => { api.validacion().then(setDatos) }, [])
  if (!datos) return <div className="grid h-64 place-items-center text-slate-400"><Loader2 className="h-6 w-6 animate-spin" /></div>

  const ok = datos.reduce((a, v) => a + v.n_ok, 0)
  const total = datos.reduce((a, v) => a + v.n_total, 0)
  const maxDif = Math.max(...datos.flatMap((v) => v.filas.filter((f) => f.tipo !== 'informativo' && f.dif_rel != null).map((f) => Math.abs(f.dif_rel!) * 100)))

  return (
    <div className="space-y-6">
      <Encabezado num={<ShieldCheck className="h-5 w-5" />} titulo="Validación del paquete" sub="Ejercicios resueltos de fuentes independientes, comparados valor por valor." />
      <Concepto titulo="¿Cómo se valida el programa?">
        <p>Un programa de diseño solo es confiable si reproduce resultados conocidos. Cada ejercicio está guardado como un
          <strong> proyecto completo</strong>: el programa lo resuelve desde cero y compara cada valor intermedio y final con el de la fuente.</p>
        <ul>
          <li><strong>Diferencia %</strong> = (app − fuente) / fuente. Diferencias pequeñas son esperables cuando la fuente redondea
            (por ejemplo, Z<sub>R</sub> = −1,405 en lugar de −1,418) o lee un nomograma.</li>
          <li><strong>Informativo:</strong> comparaciones que se muestran pero no cuentan como falla, porque la diferencia viene de un error
            de la propia fuente (el programa lo detecta y lo explica).</li>
        </ul>
      </Concepto>

      <Kpis>
        <Kpi destacado etiqueta="Ejercicios aprobados" valor={`${datos.filter((v) => v.aprobado).length} / ${datos.length}`} sub="cátedra + bibliografía" />
        <Kpi etiqueta="Valores dentro de tolerancia" valor={`${ok} / ${total}`} sub="intermedios y finales" />
        <Kpi etiqueta="Mayor diferencia" valor={`${num(maxDif, 2)} %`} sub="entre valores comparados" />
        <Kpi etiqueta="Fuentes" valor={String(new Set(datos.map((v) => v.fuente.tipo)).size)} sub="tipos de fuente independientes" />
      </Kpis>

      <div className="space-y-3">{datos.map((v) => <Ejercicio key={v.id} v={v} />)}</div>
    </div>
  )
}

function Ejercicio({ v }: { v: V }) {
  const [abierto, setAbierto] = useState(false)
  const [pdf, setPdf] = useState(false)
  const { reemplazar, ir } = useApp()
  const notas = v.filas.filter((f) => f.tipo === 'informativo' && !f.cumple)
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <button onClick={() => setAbierto(!abierto)} className="flex w-full items-center gap-4 px-5 py-4 text-left hover:bg-slate-50/60">
        {v.aprobado ? <CheckCircle2 className="h-6 w-6 shrink-0 text-emerald-500" /> : <XCircle className="h-6 w-6 shrink-0 text-red-500" />}
        <div className="min-w-0 flex-1">
          <div className="text-[15px] font-semibold text-slate-900">{v.fuente.titulo}</div>
          <div className="text-[13px] text-slate-500">{v.fuente.tipo} · {v.fuente.referencia}</div>
        </div>
        <span className={cx('num rounded-full px-2.5 py-1 text-[12.5px]', v.aprobado ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700')}>{v.n_ok}/{v.n_total}</span>
        <ChevronDown className={cx('h-4 w-4 text-slate-400 transition', abierto && 'rotate-180')} />
      </button>
      {abierto && (
        <div className="border-t border-slate-100">
          {v.proyecto.descripcion && <p className="px-5 pt-4 text-[13.5px] text-slate-600">{v.proyecto.descripcion}</p>}
          <div className="p-5 pt-3">
            <Tabla>
              <thead><tr>
                <th className={cx(th, 'w-8')} /><th className={th}>Valor</th><th className={th}>Unidad</th>
                <th className={cx(th, 'text-right')}>Fuente</th><th className={cx(th, 'text-right')}>App</th>
                <th className={cx(th, 'text-right')}>Diferencia</th><th className={cx(th, 'text-right')}>Tolerancia</th><th className={th}>Nota</th>
              </tr></thead>
              <tbody>{v.filas.map((f, i) => (
                <tr key={i}>
                  <td className={td}>{f.cumple ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : f.tipo === 'informativo' ? <Info className="h-4 w-4 text-sky-500" /> : <XCircle className="h-4 w-4 text-red-500" />}</td>
                  <td className={td}>{f.etiqueta}</td>
                  <td className={cx(td, 'text-slate-500')}>{f.unidad ?? ''}</td>
                  <td className={tdNum}>{auto(f.valor)}</td>
                  <td className={tdNum}>{auto(f.app)}</td>
                  <td className={tdNum}>{f.dif_rel == null ? '—' : `${num(f.dif_rel * 100, 2)} %`}</td>
                  <td className={cx(tdNum, 'text-slate-400')}>± {num(f.tol_rel * 100, 1)} %</td>
                  <td className={cx(td, 'max-w-md text-[12.5px] text-slate-500')}>{f.nota ?? ''}</td>
                </tr>
              ))}</tbody>
            </Tabla>
            {notas.length > 0 && (
              <div className="mt-4 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-[13.5px] text-sky-900">
                <b>Discrepancias atribuibles a la fuente</b> (no cuentan como falla):
                <ul className="mt-1 list-disc pl-5">{notas.map((x, i) => <li key={i}>{x.etiqueta}: {x.nota || 'diferencia por redondeos de la fuente.'}</li>)}</ul>
              </div>
            )}
            <div className="mt-4 flex gap-2">
              <Boton variante="oscuro" icono={<Upload className="h-4 w-4" />} onClick={() => { reemplazar(v.proyecto); ir('transito') }}>Cargar este ejercicio en la app</Boton>
              <Boton icono={pdf ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileDown className="h-4 w-4" />} disabled={pdf}
                onClick={async () => { setPdf(true); try { await descargar('pdf', v.proyecto) } finally { setPdf(false) } }}>Memoria PDF de este ejercicio</Boton>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
