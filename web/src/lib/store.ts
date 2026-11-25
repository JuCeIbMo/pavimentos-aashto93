// Estado global: un único proyecto (JSON) y su resultado, que se recalcula en la API
// cada vez que el proyecto cambia. Así los módulos quedan siempre conectados.
import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'
import { api } from './api'
import type { Proyecto, Resultado } from './tipos'

export type Pagina =
  | 'inicio' | 'transito' | 'subrasante' | 'diseno' | 'clima' | 'sensibilidad' | 'validacion' | 'referencias'

const CLAVE_LOCAL = 'pavimentos.proyecto.v2'
const PAGINAS: Pagina[] = ['inicio', 'transito', 'subrasante', 'diseno', 'clima', 'sensibilidad', 'validacion', 'referencias']

function paginaDeHash(): Pagina {
  const h = window.location.hash.replace(/^#\/?/, '') as Pagina
  return PAGINAS.includes(h) ? h : 'inicio'
}

interface Estado {
  proyecto: Proyecto | null
  resultado: Resultado | null
  resolviendo: boolean
  error: string | null
  pagina: Pagina
  /** cambia al cargar otro proyecto: los campos locales se reinician */
  version: number
  iniciar: () => Promise<void>
  editar: (fn: (p: Proyecto) => void) => void
  reemplazar: (p: Proyecto) => void
  ir: (p: Pagina) => void
}

let temporizador: ReturnType<typeof setTimeout> | undefined
let pedido = 0

export const useApp = create<Estado>()(
  immer((set, get) => {
    const resolver = () => {
      clearTimeout(temporizador)
      temporizador = setTimeout(async () => {
        const p = get().proyecto
        if (!p) return
        const id = ++pedido
        set((s) => { s.resolviendo = true })
        try {
          const r = await api.resolver(p)
          if (id === pedido) set((s) => { s.resultado = r; s.error = null; s.resolviendo = false })
        } catch (e) {
          if (id === pedido) set((s) => { s.error = (e as Error).message; s.resolviendo = false })
        }
        try { localStorage.setItem(CLAVE_LOCAL, JSON.stringify(p)) } catch { /* sin espacio */ }
      }, 120)
    }

    window.addEventListener('hashchange', () => set((s) => { s.pagina = paginaDeHash() }))

    return {
      proyecto: null,
      resultado: null,
      resolviendo: false,
      error: null,
      pagina: paginaDeHash(),
      version: 0,
      iniciar: async () => {
        let p: Proyecto | null = null
        try {
          const guardado = localStorage.getItem(CLAVE_LOCAL)
          if (guardado) p = JSON.parse(guardado)
        } catch { /* ignorar */ }
        if (!p) p = await api.inicial()
        set((s) => { s.proyecto = p })
        resolver()
      },
      editar: (fn) => {
        set((s) => { if (s.proyecto) fn(s.proyecto as Proyecto) })
        resolver()
      },
      reemplazar: (p) => {
        set((s) => { s.proyecto = p; s.version += 1 })
        resolver()
      },
      ir: (p) => {
        window.location.hash = `/${p}`
        set((s) => { s.pagina = p })
        window.scrollTo({ top: 0 })
      },
    }
  }),
)

/** Atajo para componentes que necesitan el proyecto ya cargado. */
export function useProyecto(): Proyecto {
  return useApp((s) => s.proyecto) as Proyecto
}
