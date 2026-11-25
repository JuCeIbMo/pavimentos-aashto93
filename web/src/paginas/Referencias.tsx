import { BookOpen } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Encabezado, Latex, Tarjeta } from '../components/ui'
import { api, type Referencias as R } from '../lib/api'

const GRUPOS: [string, string[]][] = [
  ['Módulo 1 · Tránsito', ['lef', 'crecimiento', 'esal']],
  ['Módulo 2 · Subrasante', ['mr_cbr', 'danio', 'mr_ef']],
  ['Módulo 4 · Diseño flexible', ['zr', 'aashto', 'e_cbr', 'coef', 'sn', 'capas']],
  ['Módulo 6 · Clima', ['hinchamiento', 'helada', 'periodo']],
]

/** Convierte *cursiva* de las referencias (formato markdown) en <em>. */
function Ref({ texto }: { texto: string }) {
  const partes = texto.split(/(\*[^*]+\*)/g)
  return <>{partes.map((p, i) => (p.startsWith('*') && p.endsWith('*') ? <em key={i}>{p.slice(1, -1)}</em> : p))}</>
}

export default function Referencias() {
  const [d, setD] = useState<R | null>(null)
  useEffect(() => { api.referencias().then(setD) }, [])
  return (
    <div className="space-y-6">
      <Encabezado num={<BookOpen className="h-5 w-5" />} titulo="Referencias y ecuaciones" sub="Bibliografía y fuente de cada ecuación implementada en el paquete." />
      <Tarjeta titulo="Bibliografía" sub="Normas APA.">
        <ul className="space-y-2.5">
          {d && Object.values(d.referencias).map((t, i) => (
            <li key={i} className="border-l-2 border-acento-300 pl-3 text-[14px] leading-relaxed text-slate-700"><Ref texto={t} /></li>
          ))}
        </ul>
      </Tarjeta>
      {d && GRUPOS.map(([titulo, claves]) => (
        <Tarjeta key={titulo} titulo={titulo}>
          <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
            {claves.map((c) => d.ecuaciones[c] && (
              <div key={c} className="rounded-xl bg-slate-50 px-4 py-3">
                <Latex tex={d.ecuaciones[c].latex} />
                <p className="mt-1 text-[13px] text-slate-600">{d.ecuaciones[c].explica}</p>
                <p className="mt-0.5 text-[12px] text-slate-400">Fuente: {d.ecuaciones[c].fuente}</p>
              </div>
            ))}
          </div>
        </Tarjeta>
      ))}
      <Tarjeta titulo="Herramientas">
        <ul className="list-disc space-y-1 pl-5 text-[14px] text-slate-700">
          <li>Motor de cálculo en Python 3 (paquete <code className="font-mono text-[13px]">pavimentos</code>), validado con pytest.</li>
          <li>API con FastAPI; interfaz web con React, TypeScript y Tailwind CSS; gráficos con Recharts; ecuaciones con KaTeX.</li>
          <li>Memoria PDF con Typst; libro Excel con fórmulas vivas con openpyxl; gráficos del PDF con matplotlib.</li>
          <li>Tablas LEF: AASHTO 93, Apéndice D (D.1–D.9), digitalizadas e interpoladas en carga y SN; tándem y trídem hasta 90 kip.</li>
        </ul>
      </Tarjeta>
    </div>
  )
}
