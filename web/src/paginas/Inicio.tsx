import { ArrowRight, CheckCircle2, CircleDashed, CloudSnow, FilePlus2, Layers, Mountain, Truck } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { CampoTexto, Tarjeta, cx } from '../components/ui'
import { api, type Fuente } from '../lib/api'
import { entero, num } from '../lib/formato'
import { useApp, useProyecto, type Pagina } from '../lib/store'
import type { Proyecto } from '../lib/tipos'

export default function Inicio() {
  const p = useProyecto()
  const { editar, resultado: r, ir, reemplazar } = useApp()
  const [ejemplos, setEjemplos] = useState<{ id: string; fuente: Fuente; proyecto: Proyecto }[]>([])
  useEffect(() => { api.ejemplos().then(setEjemplos) }, [])

  const pasos: { id: Pagina; n: string; titulo: string; desc: string; icono: ReactNode; ok: boolean | null; valor: string }[] = [
    { id: 'transito', n: '1', titulo: 'Tránsito', desc: 'Ejes equivalentes W18', icono: <Truck className="h-5 w-5" />, ok: !!r?.transito,
      valor: r?.transito ? `W18 = ${entero(r.transito.w18)}` : 'Falta la composición vehicular' },
    { id: 'subrasante', n: '2', titulo: 'Subrasante', desc: 'Módulo resiliente efectivo', icono: <Mountain className="h-5 w-5" />, ok: !!r?.subrasante,
      valor: r?.subrasante ? `MR = ${entero(r.subrasante.mr_efectivo)} psi` : 'Faltan los períodos' },
    { id: 'diseno', n: '4', titulo: 'Diseño flexible', desc: 'SN y espesores', icono: <Layers className="h-5 w-5" />, ok: !!r?.capas,
      valor: r?.capas ? r.capas.capas.map((c) => num(c.d, 1)).join(' / ') + ` ${r.capas.unidad}` : 'Completá los datos' },
    { id: 'clima', n: '6', titulo: 'Clima', desc: 'Vida útil por hinchamiento y helada', icono: <CloudSnow className="h-5 w-5" />,
      ok: p.clima.activo ? !!r?.clima : null, valor: r?.clima ? `${num(r.clima.periodo, 1)} años` : p.clima.activo ? 'Revisar' : 'No considerado' },
  ]

  return (
    <div className="space-y-8">
      <section className="max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-[28px]">Diseño de pavimentos flexibles</h1>
        <p className="mt-1.5 text-[15px] leading-relaxed text-slate-600">
          Método AASHTO 1993. Completá los módulos en orden; cada resultado pasa al siguiente.
          Al terminar, exportá la memoria de cálculo en PDF o el libro en Excel.
        </p>
      </section>

      <div>
        <h2 className="mb-3 text-[15px] font-semibold text-slate-900">Flujo de cálculo</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          {pasos.map((s, i) => (
            <button key={s.id} onClick={() => ir(s.id)}
              className="group relative rounded-2xl border border-slate-200 bg-white p-5 text-left transition-colors hover:border-acento-400">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 group-hover:text-acento-700">{s.icono}</span>
                {s.ok === true ? <CheckCircle2 className="h-5 w-5 text-emerald-500" /> : <CircleDashed className="h-5 w-5 text-slate-300" />}
              </div>
              <div className="mt-4 text-[12.5px] text-slate-500">Módulo {s.n}</div>
              <div className="text-[16px] font-semibold text-slate-900">{s.titulo}</div>
              <div className="text-[13px] text-slate-500">{s.desc}</div>
              <div className={cx('mt-3 font-mono text-[13.5px]', s.ok ? 'text-slate-800' : 'text-slate-400')}>{s.valor}</div>
              {i < pasos.length - 1 && <ArrowRight className="absolute -right-2.5 top-1/2 z-10 hidden h-5 w-5 -translate-y-1/2 rounded-full bg-slate-50 p-0.5 text-slate-300 xl:block" />}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr_1fr]">
        <Tarjeta titulo="Datos del proyecto" sub="Aparecen en la portada de la memoria de cálculo.">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2"><CampoTexto etiqueta="Nombre del proyecto" valor={p.nombre} alCambiar={(v) => editar((x) => { x.nombre = v })} /></div>
            <CampoTexto etiqueta="Autor / proyectista" valor={p.autor} alCambiar={(v) => editar((x) => { x.autor = v })} />
            <CampoTexto etiqueta="Ubicación" valor={p.ubicacion} alCambiar={(v) => editar((x) => { x.ubicacion = v })} />
            <div className="md:col-span-2"><CampoTexto area etiqueta="Descripción" valor={p.descripcion} alCambiar={(v) => editar((x) => { x.descripcion = v })} /></div>
          </div>
        </Tarjeta>

        <Tarjeta titulo="Empezar desde un ejemplo" sub="Ejercicios validados: cargalos y recorrelos módulo por módulo.">
          <div className="space-y-2">
            {ejemplos.map((e) => (
              <button key={e.id} onClick={() => { reemplazar(e.proyecto); ir('transito') }}
                className="flex w-full items-center gap-3 rounded-xl border border-slate-200 px-4 py-3 text-left transition hover:border-acento-400">
                <span className="num w-6 shrink-0 text-center text-[13px] text-slate-400">{Number(e.id.slice(0, 2))}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[14px] font-medium text-slate-800">{e.fuente.titulo}</span>
                  <span className="block text-[12.5px] text-slate-500">{e.fuente.tipo}</span>
                </span>
                <ArrowRight className="h-4 w-4 text-slate-300" />
              </button>
            ))}
            <button onClick={async () => { reemplazar(await api.nuevo()); ir('transito') }}
              className="flex w-full items-center gap-3 rounded-xl border border-dashed border-slate-300 px-4 py-3 text-left transition hover:border-slate-400 hover:bg-slate-50">
              <span className="grid w-6 place-items-center text-slate-400"><FilePlus2 className="h-4 w-4" /></span>
              <span className="flex-1 text-[14px] font-medium text-slate-700">Proyecto en blanco</span>
            </button>
          </div>
        </Tarjeta>
      </div>
    </div>
  )
}
