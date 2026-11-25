import { entero, num } from '../lib/formato'
import type { ResCapas } from '../lib/tipos'

const COLORES = ['#334155', '#d6b46b', '#e8dcc0']
const TEXTO = ['#ffffff', '#3f2d0a', '#3f2d0a']
const NOMBRES = ['Carpeta asfáltica', 'Base granular', 'Subbase granular']

/** Corte del paquete estructural dibujado a escala (alto proporcional a los espesores). */
export default function Estructura({ capas, mr }: { capas: ResCapas; mr: number }) {
  const total = capas.capas.reduce((a, c) => a + c.d_cm, 0) || 1
  const alto = 300
  const minimo = 38
  // alturas proporcionales con un mínimo legible, reescaladas para sumar `alto`
  let hs = capas.capas.map((c) => Math.max(minimo, (alto * c.d_cm) / total))
  const k = alto / hs.reduce((a, b) => a + b, 0)
  hs = hs.map((h) => h * k)
  const u = capas.unidad
  let y = 0
  return (
    <svg viewBox="0 0 420 372" className="w-full">
      <defs>
        <pattern id="suelo" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="10" height="10" fill="#d6d3d1" />
          <line x1="0" y1="0" x2="0" y2="10" stroke="#a8a29e" strokeWidth="2" />
        </pattern>
        <pattern id="grava" width="14" height="14" patternUnits="userSpaceOnUse">
          <circle cx="3" cy="4" r="1.3" fill="rgba(0,0,0,0.13)" />
          <circle cx="10" cy="10" r="1.6" fill="rgba(0,0,0,0.1)" />
        </pattern>
      </defs>
      {/* superficie */}
      <rect x="20" y="4" width="290" height="4" rx="2" fill="#0f172a" />
      {capas.capas.map((c, i) => {
        const y0 = 8 + y
        y += hs[i]
        return (
          <g key={i}>
            <rect x="20" y={y0} width="290" height={hs[i]} fill={COLORES[i]} />
            {i > 0 && <rect x="20" y={y0} width="290" height={hs[i]} fill="url(#grava)" />}
            <text x="34" y={y0 + hs[i] / 2 - 3} fill={TEXTO[i]} fontSize="13" fontWeight="600">{NOMBRES[i]}</text>
            <text x="34" y={y0 + hs[i] / 2 + 13} fill={TEXTO[i]} fontSize="11.5" opacity="0.8" fontFamily="JetBrains Mono Variable, monospace">
              a = {num(c.a, 3)}{i > 0 ? ` · m = ${num(c.m, 2)}` : ''}
            </text>
            <line x1="318" y1={y0 + 1} x2="318" y2={y0 + hs[i] - 1} stroke="#94a3b8" />
            <line x1="314" y1={y0 + 1} x2="322" y2={y0 + 1} stroke="#94a3b8" />
            <line x1="314" y1={y0 + hs[i] - 1} x2="322" y2={y0 + hs[i] - 1} stroke="#94a3b8" />
            <text x="330" y={y0 + hs[i] / 2 + 1} fontSize="16" fontWeight="700" fill="#0f172a" fontFamily="JetBrains Mono Variable, monospace">
              {num(c.d, u === 'cm' ? 1 : 1)}
              <tspan fontSize="11" fontWeight="500" fill="#64748b"> {u}</tspan>
            </text>
            <text x="330" y={y0 + hs[i] / 2 + 16} fontSize="10.5" fill="#94a3b8" fontFamily="JetBrains Mono Variable, monospace">
              {u === 'cm' ? `${num(c.d_pulg, 2)}"` : `${num(c.d_cm, 1)} cm`}
            </text>
          </g>
        )
      })}
      <rect x="20" y={8 + alto} width="290" height="48" fill="url(#suelo)" />
      <text x="34" y={8 + alto + 22} fontSize="13" fontWeight="600" fill="#44403c">Subrasante</text>
      <text x="34" y={8 + alto + 38} fontSize="11.5" fill="#57534e" fontFamily="JetBrains Mono Variable, monospace">MR = {entero(mr)} psi</text>
    </svg>
  )
}
