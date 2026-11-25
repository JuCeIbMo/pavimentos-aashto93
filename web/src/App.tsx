import {
  BookOpen, CheckCircle2, CircleDashed, CloudSnow, FileDown, FileSpreadsheet, FolderOpen, Gauge, House, Layers,
  Loader2, Mountain, Save, ShieldCheck, Truck, TriangleAlert,
} from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { cx } from './components/ui'
import { descargar, guardarBlob } from './lib/api'
import { entero, num } from './lib/formato'
import { useApp, type Pagina } from './lib/store'
import type { Proyecto, Resultado } from './lib/tipos'
import Clima from './paginas/Clima'
import Diseno from './paginas/Diseno'
import Inicio from './paginas/Inicio'
import Referencias from './paginas/Referencias'
import Sensibilidad from './paginas/Sensibilidad'
import Subrasante from './paginas/Subrasante'
import Transito from './paginas/Transito'
import Validacion from './paginas/Validacion'

interface ItemNav { id: Pagina; num?: string; titulo: string; icono: ReactNode; estado?: (r: Resultado | null, p: Proyecto) => boolean | null }

const MODULOS: ItemNav[] = [
  { id: 'transito', num: '1', titulo: 'Tránsito', icono: <Truck className="h-4 w-4" />, estado: (r) => !!r?.transito },
  { id: 'subrasante', num: '2', titulo: 'Subrasante', icono: <Mountain className="h-4 w-4" />, estado: (r) => !!r?.subrasante },
  { id: 'diseno', num: '4', titulo: 'Diseño flexible', icono: <Layers className="h-4 w-4" />, estado: (r) => !!r?.capas },
  { id: 'clima', num: '6', titulo: 'Clima', icono: <CloudSnow className="h-4 w-4" />, estado: (r, p) => (p.clima.activo ? !!r?.clima : null) },
]
const HERRAMIENTAS: ItemNav[] = [
  { id: 'sensibilidad', titulo: 'Sensibilidad', icono: <Gauge className="h-4 w-4" /> },
  { id: 'validacion', titulo: 'Validación', icono: <ShieldCheck className="h-4 w-4" /> },
  { id: 'referencias', titulo: 'Referencias', icono: <BookOpen className="h-4 w-4" /> },
]

function nombreArchivo(nombre: string) {
  return (nombre || 'proyecto').normalize('NFKD').replace(/[^\w\- ]/g, '').trim().replace(/\s+/g, '_').slice(0, 60) || 'proyecto'
}

function Sidebar() {
  const { pagina, ir, resultado, proyecto } = useApp()
  const p = proyecto as Proyecto
  const enlace = (it: ItemNav) => {
    const est = it.estado?.(resultado, p)
    const activo = pagina === it.id
    return (
      <button key={it.id} onClick={() => ir(it.id)}
        className={cx('group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-[14px] transition',
          activo ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200')}>
        <span className={cx('grid h-7 w-7 place-items-center', activo ? 'text-acento-400' : 'text-slate-500 group-hover:text-slate-300')}>
          {it.icono}
        </span>
        <span className="flex-1">
          {it.num && <span className="num mr-1.5 text-[13px] text-slate-500">{it.num}</span>}
          {it.titulo}
        </span>
        {est === true && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
        {est === false && <CircleDashed className="h-4 w-4 text-slate-500" />}
      </button>
    )
  }
  return (
    <aside className="fixed inset-y-0 left-0 z-20 flex w-64 flex-col bg-slate-950 px-3 py-4">
      <button onClick={() => ir('inicio')} className="mb-6 flex items-center gap-3 px-2 text-left">
        <div className="flex h-10 w-10 flex-col justify-center gap-[3px] rounded-xl bg-slate-800 px-2">
          <span className="h-[5px] rounded-sm bg-acento-500" />
          <span className="h-[5px] rounded-sm bg-base" />
          <span className="h-[5px] rounded-sm bg-subbase" />
        </div>
        <div>
          <div className="text-[15px] font-semibold tracking-tight text-white">Pavimentos</div>
          <div className="text-[12px] text-slate-500">AASHTO 93 · Flexibles</div>
        </div>
      </button>
      <nav className="space-y-0.5">
        {enlace({ id: 'inicio', titulo: 'Inicio', icono: <House className="h-4 w-4" /> })}
        <div className="px-3 pb-1.5 pt-5 text-[12px] font-medium text-slate-500">Módulos de cálculo</div>
        {MODULOS.map(enlace)}
        <div className="px-3 pb-1.5 pt-5 text-[12px] font-medium text-slate-500">Herramientas</div>
        {HERRAMIENTAS.map(enlace)}
      </nav>
      <div className="mt-auto px-3 text-[12px] leading-relaxed text-slate-500">
        Carreteras II · Proyecto final
        <br />
        Método AASHTO 1993
      </div>
    </aside>
  )
}

function BarraSuperior() {
  const { proyecto, resultado, resolviendo, error, reemplazar } = useApp()
  const p = proyecto as Proyecto
  const [exportando, setExportando] = useState<'pdf' | 'excel' | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const archivo = useRef<HTMLInputElement>(null)
  const completo = !!resultado?.capas
  const errores = resultado?.avisos.filter((a) => a.nivel === 'error').length ?? 0

  const exportar = async (t: 'pdf' | 'excel') => {
    setExportando(t)
    setMsg(null)
    try { await descargar(t, p) } catch (e) { setMsg((e as Error).message) } finally { setExportando(null) }
  }
  const abrir = async (f: File) => {
    try {
      const d = JSON.parse(await f.text())
      if (!d.transito || !d.diseno) throw new Error('El archivo no es un proyecto de esta app.')
      reemplazar(d)
    } catch (e) { setMsg((e as Error).message) }
  }

  return (
    <div className="sticky top-0 z-10 border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-4 px-8">
        <div className="min-w-0 flex-1">
          <div className="truncate text-[14px] font-semibold text-slate-900">{p.nombre || 'Proyecto sin título'}</div>
          <div className="flex items-center gap-1.5 text-[12px] text-slate-500">
            {resolviendo ? <><Loader2 className="h-3 w-3 animate-spin" /> Calculando…</>
              : error ? <><TriangleAlert className="h-3 w-3 text-red-500" /> Sin conexión con el motor de cálculo</>
                : errores ? <><TriangleAlert className="h-3 w-3 text-red-500" /> {errores} error{errores > 1 ? 'es' : ''} en los datos</>
                  : completo ? <><CheckCircle2 className="h-3 w-3 text-emerald-500" /> Diseño completo · W18 = {entero(resultado!.diseno!.w18)} · SN = {num(resultado!.diseno!.sn_requerido, 2)} · el PDF y el Excel salen con estos datos</>
                    : <><CircleDashed className="h-3 w-3" /> Diseño incompleto</>}
          </div>
        </div>
        {msg && <span className="max-w-xs truncate text-[12.5px] text-red-600" title={msg}>{msg}</span>}
        <div className="flex items-center gap-1.5">
          <button onClick={() => archivo.current?.click()} title="Abrir un proyecto guardado (.json)"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-[13.5px] font-medium text-slate-600 hover:bg-slate-100">
            <FolderOpen className="h-4 w-4" /> Abrir
          </button>
          <input ref={archivo} type="file" accept=".json,application/json" className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) abrir(f); e.target.value = '' }} />
          <button title="Guardar el proyecto como archivo .json"
            onClick={() => guardarBlob(new Blob([JSON.stringify(p, null, 2)], { type: 'application/json' }), `${nombreArchivo(p.nombre)}.json`)}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-[13.5px] font-medium text-slate-600 hover:bg-slate-100">
            <Save className="h-4 w-4" /> Guardar
          </button>
          <span className="mx-1.5 h-6 w-px bg-slate-200" />
          <button disabled={!completo || !!exportando} onClick={() => exportar('excel')}
            title={completo ? 'Libro Excel con fórmulas vivas' : 'Completá el diseño para exportar'}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-[13.5px] font-medium text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50 disabled:opacity-40">
            {exportando === 'excel' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4 text-emerald-600" />} Excel
          </button>
          <button disabled={!completo || !!exportando} onClick={() => exportar('pdf')}
            title={completo ? 'Memoria de cálculo en PDF' : 'Completá el diseño para exportar'}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-slate-900 px-3.5 text-[13.5px] font-medium text-white hover:bg-slate-800 disabled:opacity-40">
            {exportando === 'pdf' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileDown className="h-4 w-4" />} Memoria PDF
          </button>
        </div>
      </div>
    </div>
  )
}

const PAGINAS: Record<Pagina, () => ReactNode> = {
  inicio: () => <Inicio />,
  transito: () => <Transito />,
  subrasante: () => <Subrasante />,
  diseno: () => <Diseno />,
  clima: () => <Clima />,
  sensibilidad: () => <Sensibilidad />,
  validacion: () => <Validacion />,
  referencias: () => <Referencias />,
}

export default function App() {
  const { proyecto, iniciar, pagina, version, error } = useApp()
  useEffect(() => { iniciar().catch(() => useApp.setState({ error: 'No se pudo conectar con la API.' })) }, [iniciar])
  if (!proyecto) {
    return (
      <div className="grid h-screen place-items-center text-slate-500">
        {error ? <div className="text-center"><TriangleAlert className="mx-auto mb-2 h-6 w-6 text-red-500" />{error}<br /><span className="text-[13px]">¿Está corriendo la API (uvicorn)?</span></div>
          : <Loader2 className="h-6 w-6 animate-spin" />}
      </div>
    )
  }
  return (
    <div className="min-h-screen pl-64">
      <Sidebar />
      <BarraSuperior />
      <main key={`${pagina}-${version}`} className="mx-auto max-w-[1400px] px-8 py-8">
        {PAGINAS[pagina]()}
      </main>
    </div>
  )
}
