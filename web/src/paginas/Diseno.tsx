import { CheckCircle2, XCircle } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import Estructura from '../components/Estructura'
import {
  Avisos, CampoNumero, CampoSelector, Concepto, Decisiones, Ecuaciones, Encabezado, Kpi, Kpis, Nota,
  Numero, Segmentado, Tabla, Tarjeta, cx, td, tdNum, th,
} from '../components/ui'
import { entero, g, num, pct } from '../lib/formato'
import { useApp, useProyecto } from '../lib/store'
import type { Capa } from '../lib/tipos'

const KG_CM2_A_PSI = 14.2233

const AYUDA = {
  r: <>Confiabilidad recomendada (AASHTO 93, tabla 2.2), urbano / rural:<br />Autopistas 85–99,9 / 80–99,9 · Arterias principales 80–99 / 75–95 · Colectoras 80–95 / 75–95 · Locales 50–80 / 50–80.</>,
  so: 'Desviación estándar global. Flexibles: 0,40–0,50 (0,45 típico; 0,49 si el tránsito es poco preciso).',
  p0: 'Serviciabilidad inicial. AASHO Road Test: 4,2 para flexibles.',
  pt: 'Serviciabilidad terminal: 2,5 o más para vías principales; 2,0 para tránsito menor.',
  etapas: 'Si se construye por etapas (p. ej. pavimento inicial + recapado), cada etapa usa R^(1/n).',
}

// AASHTO 93, tabla 2.4: m por calidad de drenaje (filas) y % del tiempo cerca de la saturación (columnas): [máx, mín]
const TABLA_M: [string, string, [number, number][]][] = [
  ['Excelente', '2 horas', [[1.40, 1.35], [1.35, 1.30], [1.30, 1.20], [1.20, 1.20]]],
  ['Bueno', '1 día', [[1.35, 1.25], [1.25, 1.15], [1.15, 1.00], [1.00, 1.00]]],
  ['Regular', '1 semana', [[1.25, 1.15], [1.15, 1.05], [1.00, 0.80], [0.80, 0.80]]],
  ['Malo', '1 mes', [[1.15, 1.05], [1.05, 0.80], [0.80, 0.60], [0.60, 0.60]]],
  ['Muy malo', 'no drena', [[1.05, 0.95], [0.95, 0.75], [0.75, 0.40], [0.40, 0.40]]],
]
const EXPOSICION = ['< 1 %', '1 – 5 %', '5 – 25 %', '> 25 %']

// Tabla 4.3 (Cabezas, 2006; AASHTO 93, tabla 2.2): confiabilidad recomendada por tipo de vía, [urbana, rural]
const TABLA_R: Record<string, { nombre: string; urbana: [number, number]; rural: [number, number] }> = {
  autopista: { nombre: 'Autopista o vía expresa', urbana: [85, 99.9], rural: [80, 99.9] },
  arteria: { nombre: 'Arteria principal', urbana: [80, 99], rural: [75, 95] },
  colectora: { nombre: 'Colectora', urbana: [80, 95], rural: [75, 95] },
  local: { nombre: 'Local', urbana: [50, 80], rural: [50, 80] },
}
const rangoTxt = ([a, b]: [number, number]) => `${num(a, a % 1 ? 1 : 0)} – ${num(b, b % 1 ? 1 : 0)}`

export default function Diseno() {
  const p = useProyecto()
  const d = p.diseno
  const editar = useApp((s) => s.editar)
  const r = useApp((s) => s.resultado)
  const tr = r?.transito
  const sub = r?.subrasante
  const di = r?.diseno
  const ca = r?.capas
  const rangoR = d.tipo_via && TABLA_R[d.tipo_via] ? TABLA_R[d.tipo_via][(d.zona ?? 'rural') as 'urbana' | 'rural'] : null

  return (
    <div className="space-y-6">
      <Encabezado num="4" titulo="Diseño de pavimentos flexibles" sub="Número estructural requerido y espesores de carpeta, base y subbase." />

      <Concepto titulo="¿Cómo funciona la ecuación AASHTO 93?">
        <p>La ecuación relaciona <strong>cuántas repeticiones de carga (W<sub>18</sub>)</strong> soporta un pavimento con su
          <strong> número estructural SN</strong> antes de perder la serviciabilidad ΔPSI, para una subrasante de módulo M<sub>R</sub> y
          con una confiabilidad R.</p>
        <ul>
          <li><strong>SN</strong> es un índice de capacidad estructural que después se traduce en espesores:
            SN = a<sub>1</sub>D<sub>1</sub> + a<sub>2</sub>m<sub>2</sub>D<sub>2</sub> + a<sub>3</sub>m<sub>3</sub>D<sub>3</sub>.</li>
          <li><strong>a<sub>i</sub></strong> (coeficiente de capa): cuánto SN aporta cada pulgada de material. Un concreto asfáltico aporta
            unas tres veces más que una base granular.</li>
          <li><strong>m<sub>i</sub></strong> (drenaje): si el agua sale rápido y la capa rara vez se satura, m &gt; 1 y la capa rinde más.</li>
          <li><strong>Confiabilidad:</strong> Z<sub>R</sub>·S<sub>o</sub> «infla» el tránsito para cubrir la incertidumbre. Con R = 50 %, Z<sub>R</sub> = 0.</li>
        </ul>
        <p><strong>Diseño por capas:</strong> cada capa protege a la de abajo. La carpeta se dimensiona como si la base fuera la subrasante
          (SN<sub>1</sub> con E<sub>B</sub>); carpeta + base, como si la subbase fuera la subrasante (SN<sub>2</sub> con E<sub>SB</sub>); y el
          conjunto, para la subrasante real (SN<sub>3</sub> con M<sub>R</sub>).</p>
      </Concepto>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Tarjeta titulo="Tránsito de diseño W18" sub="Por defecto se toma del módulo 1.">
          <Segmentado valor={d.fuente_w18} alCambiar={(v) => editar((p) => { p.diseno.fuente_w18 = v; if (v === 'dato' && p.diseno.w18_dato == null) p.diseno.w18_dato = Math.round(tr?.w18 ?? 1e6) })}
            opciones={[{ valor: 'calculado', etiqueta: 'Del módulo 1' }, { valor: 'dato', etiqueta: 'Dato conocido' }]} />
          <div className="mt-4">
            {d.fuente_w18 === 'dato'
              ? <CampoNumero etiqueta="W18 (ESAL)" valor={d.w18_dato} dec={0} alCambiar={(v) => editar((p) => { p.diseno.w18_dato = v })} />
              : <ValorGrande valor={tr ? entero(tr.w18) : '—'} unidad="ESAL" falta={!tr && 'Falta calcular el módulo 1.'} />}
          </div>
        </Tarjeta>
        <Tarjeta titulo="Módulo resiliente MR" sub="Por defecto se toma el MR efectivo del módulo 2.">
          <Segmentado valor={d.fuente_mr} alCambiar={(v) => editar((p) => { p.diseno.fuente_mr = v; if (v === 'dato' && p.diseno.mr_dato == null) p.diseno.mr_dato = Math.round(sub?.mr_efectivo ?? 7000) })}
            opciones={[{ valor: 'calculado', etiqueta: 'Del módulo 2' }, { valor: 'dato', etiqueta: 'Dato conocido' }]} />
          <div className="mt-4">
            {d.fuente_mr === 'dato'
              ? <CampoNumero etiqueta="MR (psi)" valor={d.mr_dato} dec={0} alCambiar={(v) => editar((p) => { p.diseno.mr_dato = v })} />
              : <ValorGrande valor={sub ? entero(sub.mr_efectivo) : '—'} unidad="psi" falta={!sub && 'Falta calcular el módulo 2.'} />}
          </div>
        </Tarjeta>
      </div>

      <Tarjeta titulo="Confiabilidad y serviciabilidad" sub="El selector de la izquierda de cada recuadro es un atajo con la tabla; el valor de la derecha es el que entra al cálculo y se puede corregir a mano.">
        <div className="grid grid-cols-1 gap-x-4 gap-y-5 xl:grid-cols-[2.4fr_1.6fr]">
          <Grupo columnas="sm:grid-cols-[1.3fr_1fr_0.9fr]">
            <CampoSelector etiqueta="Tipo de vía (tabla 4.3)" valor={d.tipo_via ?? 'otro'}
              opciones={[...Object.entries(TABLA_R).map(([k, v]) => ({ valor: k, etiqueta: v.nombre })), { valor: 'otro', etiqueta: 'Otro (a mano)' }]}
              alCambiar={(v) => editar((p) => { p.diseno.tipo_via = v === 'otro' ? null : v; aplicarR(p.diseno) })} />
            <CampoSelector etiqueta="Zona" valor={d.zona ?? 'rural'}
              opciones={[{ valor: 'urbana', etiqueta: 'Urbana' }, { valor: 'rural', etiqueta: 'Rural' }]}
              alCambiar={(v) => editar((p) => { p.diseno.zona = v; aplicarR(p.diseno) })} />
            <div>
              <CampoNumero etiqueta="R (%)" ayuda={AYUDA.r} valor={d.r_pct} dec={1} min={rangoR?.[0] ?? 50} max={rangoR?.[1] ?? 99.99}
                alCambiar={(v) => editar((p) => { p.diseno.r_pct = v ?? 50 })} />
              <Pista>{rangoR ? `Tabla 4.3: ${rangoTxt(rangoR)} %` : 'Elegí el tipo de vía'}</Pista>
            </div>
          </Grupo>
          <Grupo columnas="sm:grid-cols-[1.4fr_1fr]">
            <CampoSelector etiqueta="Errores en el tránsito (tabla 4.2)" valor={d.so === 0.49 ? 'con' : d.so === 0.44 ? 'sin' : 'otro'}
              opciones={[{ valor: 'con', etiqueta: 'Con errores (0,49)' }, { valor: 'sin', etiqueta: 'Sin errores (0,44)' }, { valor: 'otro', etiqueta: 'Otro valor (a mano)' }]}
              alCambiar={(v) => { if (v !== 'otro') editar((p) => { p.diseno.so = v === 'con' ? 0.49 : 0.44 }) }} />
            <div>
              <CampoNumero etiqueta="So" ayuda={AYUDA.so} valor={d.so} min={0.4} max={0.5}
                alCambiar={(v) => editar((p) => { p.diseno.so = v ?? 0.45 })} />
              <Pista>Flexible: 0,40 – 0,50</Pista>
            </div>
          </Grupo>
          <Grupo columnas="sm:grid-cols-[1.3fr_1fr_0.9fr]">
            <CampoSelector etiqueta="Importancia de la vía" valor={d.pt === 2.5 ? 'principal' : d.pt === 2 ? 'menor' : 'otro'}
              opciones={[{ valor: 'principal', etiqueta: 'Vía principal (pt 2,5)' }, { valor: 'menor', etiqueta: 'Tránsito menor (pt 2,0)' }, { valor: 'otro', etiqueta: 'Otro valor (a mano)' }]}
              alCambiar={(v) => { if (v !== 'otro') editar((p) => { p.diseno.pt = v === 'principal' ? 2.5 : 2 }) }} />
            <div>
              <CampoNumero etiqueta="p0 inicial" ayuda={AYUDA.p0} valor={d.p0} dec={1} min={3} max={5}
                alCambiar={(v) => editar((p) => { p.diseno.p0 = v ?? 4.2 })} />
              <Pista>Flexible: 4,2</Pista>
            </div>
            <div>
              <CampoNumero etiqueta="pt terminal" ayuda={AYUDA.pt} valor={d.pt} dec={1} min={1.5} max={3.5}
                alCambiar={(v) => editar((p) => { p.diseno.pt = v ?? 2.5 })} />
              <Pista>ΔPSI = {num(d.p0 - d.pt, 2)}</Pista>
            </div>
          </Grupo>
          <Grupo columnas="grid-cols-1">
            <div>
              <CampoNumero etiqueta="Etapas de construcción" ayuda={AYUDA.etapas} valor={d.etapas} dec={0} min={1} max={4}
                alCambiar={(v) => editar((p) => { p.diseno.etapas = Math.max(1, Math.round(v ?? 1)) })} />
              {di && <Pista>Z<sub>R</sub> = {num(di.zr, 3)}{di.etapas > 1 && <> · R por etapa = R<sup>1/{di.etapas}</sup> = {pct(di.r_etapa, 2)}</>}</Pista>}
            </div>
          </Grupo>
        </div>
      </Tarjeta>

      <Tarjeta titulo="Materiales" sub="Coeficientes estructurales a partir del módulo de cada material (o ingresados directamente).">
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          <Carpeta />
          <Granular titulo="Base granular" clave="base" color="bg-base" />
          <Granular titulo="Subbase granular" clave="subbase" color="bg-subbase" />
        </div>
        <Drenaje />
      </Tarjeta>

      <Tarjeta titulo="Criterios de redondeo y espesores mínimos">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <CampoSelector etiqueta="Unidad de espesores" valor={d.unidad} alCambiar={(v) => editar((p) => { p.diseno.unidad = v })}
            opciones={[{ valor: 'cm', etiqueta: 'centímetros' }, { valor: 'pulg', etiqueta: 'pulgadas' }]} />
          <CampoNumero etiqueta={`Redondear espesores a (${d.unidad})`} ayuda="Siempre hacia arriba." valor={d.paso_espesor} min={0.1}
            alCambiar={(v) => editar((p) => { p.diseno.paso_espesor = v ?? 0.5 })} />
          <CampoNumero etiqueta="Redondear SN a" ayuda="0 = no redondear. Lo habitual es adoptar el SN redondeado hacia arriba a 0,1." valor={d.paso_sn}
            alCambiar={(v) => editar((p) => { p.diseno.paso_sn = v ?? 0 })} />
          <CampoSelector etiqueta="Espesores mínimos" valor={d.minimos} alCambiar={(v) => editar((p) => { p.diseno.minimos = v })}
            opciones={[{ valor: 'aashto', etiqueta: 'Tabla AASHTO (según W18)' }, { valor: 'personalizado', etiqueta: 'Personalizados' }, { valor: 'ninguno', etiqueta: 'Sin mínimos' }]} />
        </div>
        {d.minimos === 'personalizado' && (
          <div className="mt-4 grid grid-cols-3 gap-4 md:w-2/3">
            <CampoNumero etiqueta={`Mínimo carpeta (${d.unidad})`} valor={d.min_carpeta} alCambiar={(v) => editar((p) => { p.diseno.min_carpeta = v ?? 0 })} />
            <CampoNumero etiqueta={`Mínimo base (${d.unidad})`} valor={d.min_base} alCambiar={(v) => editar((p) => { p.diseno.min_base = v ?? 0 })} />
            <CampoNumero etiqueta={`Mínimo subbase (${d.unidad})`} valor={d.min_subbase} alCambiar={(v) => editar((p) => { p.diseno.min_subbase = v ?? 0 })} />
          </div>
        )}
        {d.minimos === 'aashto' && (
          <p className="mt-3 text-[12.5px] text-slate-500">
            Tabla AASHTO 93 (Parte II, 3.1.5), carpeta / base: W18 ≤ 50.000 → 1" / 4" · ≤ 150.000 → 2" / 4" · ≤ 500.000 → 2,5" / 4" ·
            ≤ 2.000.000 → 3" / 6" · ≤ 7.000.000 → 3,5" / 6" · más → 4" / 6".
          </p>
        )}
      </Tarjeta>

      <Avisos modulo="diseno" />

      {di && ca && (
        <>
          <Kpis>
            <Kpi destacado etiqueta="SN requerido" valor={num(di.sn_requerido, 3)} sub={`adoptado ${num(di.sn_adoptado, 2)}`} />
            <Kpi etiqueta="SN aportado" valor={num(ca.sn_total, 3)} sub={ca.cumple ? '✓ cumple' : '✗ no cumple'} />
            <Kpi etiqueta="Espesor total" valor={`${num(ca.espesor_total, 1)} ${ca.unidad}`} sub={`W usado: ${entero(ca.w_diseno)}`} />
            <Kpi etiqueta="ZR · So" valor={num(di.zr * di.so, 3)} sub={`ZR = ${num(di.zr, 3)} · So = ${g(di.so)}`} />
          </Kpis>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[400px_1fr]">
            <Tarjeta titulo="Estructura adoptada" sub="Dibujo a escala.">
              <Estructura capas={ca} mr={di.mr} />
            </Tarjeta>
            <Tarjeta titulo="Diseño por capas" pad={false}>
              <Tabla>
                <thead>
                  <tr>
                    <th className={th}>Capa</th>
                    <th className={cx(th, 'text-right')}>a</th>
                    <th className={cx(th, 'text-right')}>m</th>
                    <th className={cx(th, 'text-right')}>SN req.</th>
                    <th className={cx(th, 'text-right')}>D calc. ({ca.unidad})</th>
                    <th className={cx(th, 'text-right')}>Mínimo</th>
                    <th className={cx(th, 'text-right')}>D adoptado</th>
                    <th className={cx(th, 'text-right')}>SN aporte</th>
                  </tr>
                </thead>
                <tbody>
                  {ca.capas.map((c, i) => (
                    <tr key={i}>
                      <td className={td}><span className={cx('mr-2 inline-block h-2.5 w-2.5 rounded-sm align-middle', ['bg-carpeta', 'bg-base', 'bg-subbase'][i])} />{c.capa}</td>
                      <td className={tdNum}>{num(c.a, 3)}</td>
                      <td className={tdNum}>{i === 0 ? '—' : num(c.m, 2)}</td>
                      <td className={tdNum}>{num(c.sn_req, 3)}</td>
                      <td className={tdNum}>{num(c.d_calc, 2)}</td>
                      <td className={tdNum}>{c.minimo ? num(c.minimo, 1) : '—'}</td>
                      <td className={cx(tdNum, 'font-semibold text-slate-900')}>{num(c.d, 1)} {ca.unidad}</td>
                      <td className={tdNum}>{num(c.sn_aporte, 3)}</td>
                    </tr>
                  ))}
                  <tr className="bg-slate-50 font-semibold">
                    <td className={td} colSpan={6}>Total</td>
                    <td className={tdNum}>{num(ca.espesor_total, 1)} {ca.unidad}</td>
                    <td className={tdNum}>{num(ca.sn_total, 3)}</td>
                  </tr>
                </tbody>
              </Tabla>
              <div className="space-y-2 p-5">
                <div className="text-[13px] font-semibold text-slate-700">Verificaciones</div>
                {ca.verificaciones.map((v, i) => (
                  <div key={i} className="flex items-center gap-2 text-[13.5px]">
                    {v.cumple ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <XCircle className="h-4 w-4 text-red-500" />}
                    <span className="text-slate-700">{v.criterio}:</span>
                    <span className="font-mono text-slate-900">{num(v.izq, 3)} ≥ {num(v.der, 3)}</span>
                  </div>
                ))}
                <p className="pt-2 text-[12.5px] text-slate-500">
                  E base = {entero(di.materiales.base.e)} psi ({di.materiales.base.origen_e}) · E subbase = {entero(di.materiales.subbase.e)} psi ({di.materiales.subbase.origen_e}) ·
                  a₁ = {num(di.materiales.carpeta.a, 4)} · a₂ = {num(di.materiales.base.a, 4)} · a₃ = {num(di.materiales.subbase.a, 4)}
                </p>
              </div>
            </Tarjeta>
          </div>
        </>
      )}

      <Decisiones modulo="diseno" />
      <Ecuaciones claves={['zr', 'aashto', 'e_cbr', 'coef', 'sn', 'capas']}>
        {di && (
          <Nota>
            Con log W18 = <b className="font-mono">{num(di.log_w18, 3)}</b>, Z<sub>R</sub> = <b className="font-mono">{num(di.zr, 3)}</b>,
            S<sub>o</sub> = <b className="font-mono">{g(di.so)}</b>, ΔPSI = <b className="font-mono">{num(di.dpsi, 2)}</b> y
            M<sub>R</sub> = <b className="font-mono">{entero(di.mr)}</b> psi, la ecuación se resuelve por bisección →
            SN = <b className="font-mono">{num(di.sn_requerido, 3)}</b>. Comprobación con el SN adoptado: log W = <b className="font-mono">{num(di.log_w_admisible, 3)}</b>.
          </Nota>
        )}
      </Ecuaciones>
    </div>
  )
}

function ValorGrande({ valor, unidad, falta }: { valor: string; unidad: string; falta?: ReactNode }) {
  if (falta) return <p className="text-[14px] text-amber-700">{falta}</p>
  return <div className="font-mono text-[26px] font-semibold text-slate-900">{valor} <span className="text-[14px] font-normal text-slate-500">{unidad}</span></div>
}

function Carpeta() {
  const p = useProyecto()
  const editar = useApp((s) => s.editar)
  const c = p.diseno.carpeta
  const [unidad, setUnidad] = useState<'kg' | 'psi'>('kg')
  const e = c.e_psi ?? 400000
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <div className="mb-3 flex items-center gap-2"><span className="h-3 w-3 rounded-sm bg-carpeta" /><span className="text-[14px] font-semibold text-slate-800">Carpeta asfáltica</span></div>
      <div className="mb-3"><Segmentado valor={unidad} alCambiar={setUnidad} opciones={[{ valor: 'kg', etiqueta: 'kg/cm²' }, { valor: 'psi', etiqueta: 'psi' }]} /></div>
      {unidad === 'kg'
        ? <CampoNumero etiqueta="E concreto asfáltico (kg/cm²)" ayuda="Módulo elástico a 20 °C. 29.880 kg/cm² ≈ 425.000 psi." valor={Math.round(e / KG_CM2_A_PSI)} dec={0}
          alCambiar={(v) => editar((p) => { if (v != null && v !== Math.round(e / KG_CM2_A_PSI)) p.diseno.carpeta.e_psi = v * KG_CM2_A_PSI })} />
        : <CampoNumero etiqueta="E concreto asfáltico (psi)" valor={e} dec={0} alCambiar={(v) => editar((p) => { p.diseno.carpeta.e_psi = v })} />}
      <CoefDirecto capa={c} etiqueta="a₁" alCambiar={(a) => editar((p) => { p.diseno.carpeta.a = a })} />
    </div>
  )
}

function Granular({ titulo, clave, color }: { titulo: string; clave: 'base' | 'subbase'; color: string }) {
  const p = useProyecto()
  const editar = useApp((s) => s.editar)
  const c = p.diseno[clave]
  const modo = c.e_psi == null ? 'cbr' : 'e'
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <div className="mb-3 flex items-center gap-2"><span className={cx('h-3 w-3 rounded-sm', color)} /><span className="text-[14px] font-semibold text-slate-800">{titulo}</span></div>
      <div className="mb-3">
        <Segmentado valor={modo} alCambiar={(v) => editar((p) => {
          const x = p.diseno[clave]
          if (v === 'cbr') { x.e_psi = null; x.cbr = x.cbr ?? (clave === 'base' ? 80 : 30) } else { x.e_psi = x.e_psi ?? 20000; x.cbr = null }
        })} opciones={[{ valor: 'cbr', etiqueta: 'CBR' }, { valor: 'e', etiqueta: 'Módulo E' }]} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        {modo === 'cbr'
          ? <CampoNumero etiqueta="CBR (%)" ayuda="El módulo se estima con la correlación de Cabezas (2006)." valor={c.cbr} dec={1}
            alCambiar={(v) => editar((p) => { p.diseno[clave].cbr = v })} />
          : <CampoNumero etiqueta="E (psi)" valor={c.e_psi} dec={0} alCambiar={(v) => editar((p) => { p.diseno[clave].e_psi = v })} />}
        <CampoNumero etiqueta={`m${clave === 'base' ? '₂' : '₃'} (drenaje)`} ayuda="Coeficiente de drenaje. Se completa con las tablas 4.12 y 4.13 de abajo, o a mano." valor={c.m} min={0.4} max={1.4}
          alCambiar={(v) => editar((p) => { p.diseno[clave].m = v ?? 1 })} />
      </div>
      <CoefDirecto capa={c} etiqueta={clave === 'base' ? 'a₂' : 'a₃'} alCambiar={(a) => editar((p) => { p.diseno[clave].a = a })} />
    </div>
  )
}

function CoefDirecto({ capa, etiqueta, alCambiar }: { capa: Capa; etiqueta: string; alCambiar: (a: number | null) => void }) {
  const activo = capa.a != null
  return (
    <div className="mt-3 flex items-center gap-3">
      <label className="flex cursor-pointer items-center gap-2 text-[13px] text-slate-600">
        <input type="checkbox" className="h-4 w-4 accent-amber-500" checked={activo} onChange={(e) => alCambiar(e.target.checked ? 0.12 : null)} />
        Ingresar {etiqueta} directo
      </label>
      {activo && <Numero compacto valor={capa.a} dec={4} className="w-28" alCambiar={(v) => alCambiar(v ?? 0)} />}
    </div>
  )
}

function Drenaje() {
  const p = useProyecto()
  const d = p.diseno
  const editar = useApp((s) => s.editar)
  const fila = d.drenaje_calidad ?? null
  const col = d.drenaje_saturacion ?? null
  const rango = fila != null && col != null ? TABLA_M[fila][2][col] : null
  const elegir = (f: number | null, c: number | null) => editar((p) => {
    p.diseno.drenaje_calidad = f
    p.diseno.drenaje_saturacion = c
    if (f != null && c != null) {
      const [hi, lo] = TABLA_M[f][2][c]
      const m = Math.round(((hi + lo) / 2) * 100) / 100
      p.diseno.base.m = m
      p.diseno.subbase.m = m
    }
  })
  return (
    <div className="mt-5 rounded-xl border border-slate-200 p-4">
      <div className="mb-3 text-[14px] font-semibold text-slate-800">Drenaje de base y subbase (m₂, m₃)</div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-[1.3fr_1.3fr_1fr]">
        <CampoSelector etiqueta="Calidad del drenaje (tabla 4.12)" valor={fila ?? -1}
          opciones={[{ valor: -1, etiqueta: 'Elegir…' }, ...TABLA_M.map(([cal, t], i) => ({ valor: i, etiqueta: `${cal} (agua eliminada en ${t})` }))]}
          alCambiar={(v) => elegir(v < 0 ? null : v, col)} />
        <CampoSelector etiqueta="% del tiempo cerca de la saturación" valor={col ?? -1}
          opciones={[{ valor: -1, etiqueta: 'Elegir…' }, ...EXPOSICION.map((e, i) => ({ valor: i, etiqueta: e }))]}
          alCambiar={(v) => elegir(fila, v < 0 ? null : v)} />
        <div className="rounded-lg bg-slate-50 px-3 py-2 text-[13px] text-slate-600">
          {rango
            ? <>Tabla 4.13: <b className="font-mono">{rango[0] === rango[1] ? num(rango[0], 2) : `${num(rango[1], 2)} – ${num(rango[0], 2)}`}</b><br />se adopta el valor medio en m₂ y m₃</>
            : 'Elegí las dos condiciones para obtener m de la tabla 4.13.'}
        </div>
      </div>
      <details className="mt-3">
        <summary className="cursor-pointer text-[13px] text-slate-500 hover:text-slate-800">Ver la tabla 4.13 completa (también se puede elegir tocando una celda)</summary>
        <div className="mt-2">
          <Tabla>
            <thead>
              <tr>
                <th className={th}>Calidad del drenaje<br /><span className="font-normal normal-case">(tiempo en eliminar el agua)</span></th>
                {EXPOSICION.map((e) => <th key={e} className={cx(th, 'text-center')}>{e}<br /><span className="font-normal normal-case">del tiempo saturada</span></th>)}
              </tr>
            </thead>
            <tbody>
              {TABLA_M.map(([cal, t, filaM], i) => (
                <tr key={cal}>
                  <td className={td}><b className="font-medium">{cal}</b> <span className="text-slate-400">({t})</span></td>
                  {filaM.map(([hi, lo], j) => (
                    <td key={j} className={cx(td, 'p-1 text-center')}>
                      <button onClick={() => elegir(i, j)}
                        className={cx('w-full rounded-md py-1.5 font-mono text-[13px] transition',
                          fila === i && col === j ? 'bg-acento-500 text-slate-950' : 'hover:bg-acento-50')}>
                        {hi === lo ? num(hi, 2) : `${num(lo, 2)} – ${num(hi, 2)}`}
                      </button>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Tabla>
          <p className="mt-2 text-[12.5px] text-slate-500">AASHTO 93, Parte II, tabla 2.4. m multiplica el aporte de las capas granulares: SN = a₁D₁ + a₂m₂D₂ + a₃m₃D₃.</p>
        </div>
      </details>
    </div>
  )
}

/** Recuadro gris: atajo con tabla + valor editable. */
function Grupo({ children, columnas }: { children: ReactNode; columnas: string }) {
  return <div className={cx('grid grid-cols-1 gap-3 rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200/70', columnas)}>{children}</div>
}

function Pista({ children }: { children: ReactNode }) {
  return <p className="mt-1 text-[11.5px] leading-tight text-slate-500">{children}</p>
}

/** Escribe en R el valor central (redondeado a 5) del rango de la tabla 4.3 para el tipo de vía y la zona. */
function aplicarR(d: { tipo_via?: string | null; zona?: string | null; r_pct: number }) {
  if (!d.tipo_via || !TABLA_R[d.tipo_via]) return
  const [a, b] = TABLA_R[d.tipo_via][(d.zona ?? 'rural') as 'urbana' | 'rural']
  d.r_pct = Math.min(b, Math.max(a, Math.round((a + b) / 2 / 5) * 5))
}
