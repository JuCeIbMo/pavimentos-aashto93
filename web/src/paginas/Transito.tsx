import { CheckCircle2, ChevronDown, CircleAlert, Copy, Plus, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import {
  Avisos, Ayuda, Barra, CampoNumero, CampoSelector, Concepto, Decisiones, Ecuaciones, Encabezado, Kpi, Kpis, Nota,
  Numero, Segmentado, Selector, Tabla, Tarjeta, cx, td, tdNum, th,
} from '../components/ui'
import { api, type OpcionCatalogo } from '../lib/api'
import { entero, g, num } from '../lib/formato'
import { useApp, useProyecto } from '../lib/store'
import type { Eje, TipoEje, Vehiculo } from '../lib/tipos'

const KIP_POR_T = 2.20462
/** AASHTO 93, Parte II 2.1.3: carriles por sentido → rango de Fc */
const FC_AASHTO: Record<number, [number, number]> = { 1: [1, 1], 2: [0.8, 1], 3: [0.6, 0.8], 4: [0.5, 0.75] }
const rango = ([a, b]: [number, number]) => (a === b ? num(a, 2) : `${num(a, 2)} – ${num(b, 2)}`)
const TIPOS: { valor: TipoEje; etiqueta: string }[] = [
  { valor: 'simple', etiqueta: 'Simple' },
  { valor: 'tandem', etiqueta: 'Tándem' },
  { valor: 'tridem', etiqueta: 'Trídem' },
]
const POSICION = ['Eje delantero', 'Eje trasero 1', 'Eje trasero 2', 'Eje trasero 3', 'Eje trasero 4', 'Eje trasero 5']

const AYUDA = {
  n: 'Años de servicio que debe cubrir esta etapa. AASHTO recomienda 10–20 años para la etapa inicial.',
  fd: 'Fracción del tránsito (ambos sentidos) que va en la dirección más cargada. AASHTO: 0,3 a 0,7; se usa 0,5 si el tránsito es parejo en los dos sentidos. Si el TPDA ya es de un solo sentido, Fd = 1.',
  fc: 'Fracción de los vehículos de esa dirección que circula por el carril de diseño (el de la derecha, por donde van los pesados). Depende de cuántos carriles hay por sentido.',
  pt: 'Serviciabilidad terminal con la que se eligen las tablas LEF (2,0; 2,5 o 3,0). Conviene igualarla al pt de diseño.',
  sn: 'Columna de las tablas LEF. Como el SN todavía no se conoce (es lo que se diseña), se supone uno; si el SN de diseño difiere en más de 0,5, se repite con la columna más cercana.',
}

export default function Transito() {
  const p = useProyecto()
  const t = p.transito
  const editar = useApp((s) => s.editar)
  const tr = useApp((s) => s.resultado?.transito)
  const u = t.unidad_carga
  const nEjes = Math.max(4, ...t.vehiculos.map((v) => v.ejes.length))
  const fcRango = FC_AASHTO[t.carriles ?? 1] ?? FC_AASHTO[1]
  const snDis = useApp((s) => s.resultado?.diseno?.sn_adoptado)
  const sug = useApp((s) => s.resultado?.sn_sugerido)
  const lejos = snDis != null && Math.abs(snDis - t.sn_lef) > 0.5

  const cambiarUnidad = (nueva: 't' | 'kip') => editar((p) => {
    if (nueva === p.transito.unidad_carga) return
    const f = nueva === 'kip' ? KIP_POR_T : 1 / KIP_POR_T
    p.transito.vehiculos.forEach((v) => { v.ejes = v.ejes.map(([tp, c]) => [tp, Math.round(c * f * 1000) / 1000] as Eje) })
    p.transito.unidad_carga = nueva
  })

  return (
    <div className="space-y-6">
      <Encabezado num="01" titulo="Cálculo de ejes equivalentes"
        sub="Convierte el TPDA y la composición vehicular en repeticiones del eje patrón de 18 kip (W18)." />

      <Concepto titulo="¿Qué es un eje equivalente y por qué importa?">
        <p>El pavimento no «ve» vehículos: ve <strong>repeticiones de carga por eje</strong>. Para sumar ejes de pesos
          distintos, AASHTO los convierte a un eje patrón de <strong>18 kip (8,2 t) en eje simple</strong> mediante el
          <strong> factor de equivalencia de carga (LEF)</strong>. El daño crece aproximadamente con la <strong>cuarta potencia</strong> de
          la carga: un eje de 16,4 t no daña el doble que uno de 8,2 t, sino unas 16 veces más.</p>
        <ul>
          <li><strong>LEF:</strong> se lee en las tablas D.1–D.9 de AASHTO según el <strong>tipo de eje</strong> (simple, tándem,
            trídem), la <strong>carga en kip</strong> (fila), el <strong>SN</strong> supuesto (columna) y el <strong>p<sub>t</sub></strong> (tabla).</li>
          <li><strong>Factor camión (F<sub>cam</sub>):</strong> suma de los LEF de todos los ejes de un vehículo.</li>
          <li><strong>ESAL del año 1:</strong> TPDA × F<sub>cam</sub> × 365 × F<sub>d</sub> × F<sub>c</sub> (solo el carril de diseño).</li>
          <li><strong>W<sub>18</sub>:</strong> ESAL acumulados en el período, con el crecimiento compuesto de cada vehículo.</li>
        </ul>
        <p><strong>¿Y el SN «supuesto»?</strong> Para leer un LEF hay que elegir la columna de SN, pero el SN es justamente lo que
          se diseña en el módulo 4. A mano se supone un SN (por ejemplo 3), se calcula W<sub>18</sub>, se diseña, y si el SN obtenido
          difiere en más de 0,5 se repite con la columna de SN más cercana. El programa te avisa cuándo hace falta.</p>
      </Concepto>

      <Tarjeta titulo="Parámetros del tránsito">
        <div className="grid grid-cols-1 gap-x-4 gap-y-5 md:grid-cols-2 xl:grid-cols-[0.8fr_2fr_2fr_0.9fr_0.9fr]">
          <CampoNumero etiqueta="Período n (años)" ayuda={AYUDA.n} valor={t.n} dec={0} min={1} max={50}
            alCambiar={(v) => editar((p) => { p.transito.n = v ?? 0 })} />
          <Grupo>
            <CampoSelector etiqueta="Reparto por sentido" ayuda="Atajo: escribe Fd. Después podés ajustarlo a mano."
              valor={t.fd === 0.5 ? 'parejo' : t.fd === 1 ? 'uno' : 'otro'}
              opciones={[{ valor: 'parejo', etiqueta: 'Parejo en ambos (0,50)' }, { valor: 'uno', etiqueta: 'TPDA de un sentido (1,00)' },
                { valor: 'otro', etiqueta: 'Otro valor (a mano)' }]}
              alCambiar={(v) => { if (v !== 'otro') editar((p) => { p.transito.fd = v === 'parejo' ? 0.5 : 1 }) }} />
            <div>
              <CampoNumero etiqueta="Fd" ayuda={AYUDA.fd} valor={t.fd} min={0.3} max={1}
                alCambiar={(v) => editar((p) => { p.transito.fd = v ?? 0 })} />
              <Pista>AASHTO: 0,30 – 0,70 (o 1,00)</Pista>
            </div>
          </Grupo>
          <Grupo>
            <CampoSelector etiqueta="Carriles por sentido" ayuda="Atajo: escribe en Fc el valor más desfavorable del rango AASHTO. Después podés ajustarlo a mano."
              valor={t.carriles ?? 1}
              opciones={[1, 2, 3, 4].map((x) => ({ valor: x, etiqueta: x === 4 ? '4 o más' : String(x) }))}
              alCambiar={(v) => editar((p) => { p.transito.carriles = v; p.transito.fc = FC_AASHTO[v][1] })} />
            <div>
              <CampoNumero etiqueta="Fc" ayuda={AYUDA.fc} valor={t.fc} min={fcRango[0]} max={fcRango[1]}
                alCambiar={(v) => editar((p) => { p.transito.fc = v ?? 0 })} />
              <Pista>AASHTO para {t.carriles === 4 ? '4 o más' : t.carriles ?? 1}: {rango(fcRango)}</Pista>
            </div>
          </Grupo>
          <CampoSelector etiqueta="pt de las tablas LEF" ayuda={AYUDA.pt} valor={t.pt}
            opciones={[2, 2.5, 3].map((x) => ({ valor: x, etiqueta: num(x, 1) }))}
            alCambiar={(v) => editar((p) => { p.transito.pt = v })} />
          <div>
            <CampoSelector etiqueta="SN supuesto (LEF)" ayuda={AYUDA.sn} valor={t.sn_lef}
              opciones={[1, 2, 3, 4, 5, 6].map((x) => ({ valor: x, etiqueta: String(x) }))}
              alCambiar={(v) => editar((p) => { p.transito.sn_lef = v })} />
            {snDis != null && (
              lejos
                ? <p className="mt-1 text-[11.5px] font-medium leading-tight text-amber-700">El diseño dio SN = {num(snDis, 1)}: elegí {sug}</p>
                : <Pista>El diseño dio SN = {num(snDis, 1)} ✓</Pista>
            )}
          </div>
        </div>
      </Tarjeta>

      <Tarjeta titulo="Composición vehicular" pad={false}
        sub="Cada vehículo con sus ejes (carga y tipo), su TPDA y su tasa de crecimiento. El nombre es solo una etiqueta."
        acciones={
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-[13px] text-slate-500">
              Cargas en
              <Segmentado valor={u} alCambiar={cambiarUnidad}
                opciones={[{ valor: 't', etiqueta: 'toneladas' }, { valor: 'kip', etiqueta: 'kip' }]} />
            </div>
            <Ayuda texto="Las tablas LEF están en kip. Si cargás toneladas se convierten con el factor exacto: 1 t = 1000 kg = 2204,6 lb = 2,2046 kip. Debajo de cada carga ves los kip con los que se entra a la tabla." />
          </div>
        }>
        <TablaVehiculos nEjes={nEjes} />
        <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 px-5 py-3">
          <AgregarVehiculo />
          <span className="text-[12.5px] text-slate-500">
            En cada eje: carga arriba, tipo abajo; debajo, los kip con que se entra a la tabla → LEF. «—» = no tiene ese eje.
          </span>
        </div>
        <EstadoCarga />
      </Tarjeta>

      <Avisos modulo="transito" excluir={(x) => x.startsWith('Fila ')} />

      {tr && (
        <>
          <Kpis>
            <Kpi destacado etiqueta="W18 de diseño" valor={entero(tr.w18)} sub={`ESAL en ${g(tr.n)} años, carril de diseño`} />
            <Kpi etiqueta="ESAL del primer año" valor={entero(tr.esal1_total)} sub="carril de diseño" />
            <Kpi etiqueta="TPDA total" valor={entero(tr.tpda_total)} sub="veh/día, ambos sentidos" />
            <Kpi etiqueta="Factores" valor={`${g(tr.fd)} × ${g(tr.fc)}`} sub="Fd × Fc" />
          </Kpis>

          <Tarjeta titulo="Resultado: ejes equivalentes por vehículo" pad={false}
            sub="Se calcula solo a partir de la tabla de arriba (no se edita). G = factor de crecimiento · ESAL año 1 = TPDA × Fcam × 365 × Fd × Fc · W = ESAL año 1 × G">
            <Tabla>
              <thead>
                <tr>
                  <th className={th}>Vehículo</th>
                  <th className={cx(th, 'text-right')}>TPDA</th>
                  <th className={cx(th, 'text-right')}>r</th>
                  <th className={cx(th, 'text-right')}>Factor camión</th>
                  <th className={cx(th, 'text-right')}>G</th>
                  <th className={cx(th, 'text-right')}>ESAL año 1</th>
                  <th className={cx(th, 'text-right')}>W ({g(tr.n)} años)</th>
                  <th className={cx(th, 'w-56')}>Aporte al W18</th>
                </tr>
              </thead>
              <tbody>
                {tr.filas.map((f, i) => (
                  <tr key={i} className="hover:bg-slate-50/60">
                    <td className={td}>{f.nombre}</td>
                    <td className={tdNum}>{entero(f.tpda)}</td>
                    <td className={tdNum}>{num(f.r * 100, 2)} %</td>
                    <td className={tdNum}>{num(f.factor_camion, 4)}{f.origen_fc === 'dato' && <span className="text-acento-600"> *</span>}</td>
                    <td className={tdNum}>{num(f.g, 3)}</td>
                    <td className={tdNum}>{entero(f.esal1)}</td>
                    <td className={tdNum}>{entero(f.w)}</td>
                    <td className={td}><Barra valor={(100 * f.w) / tr.w18} /></td>
                  </tr>
                ))}
                <tr className="bg-slate-50 font-semibold">
                  <td className={td}>Total</td>
                  <td className={tdNum}>{entero(tr.tpda_total)}</td>
                  <td className={td} colSpan={3} />
                  <td className={tdNum}>{entero(tr.esal1_total)}</td>
                  <td className={cx(tdNum, 'text-acento-700')}>{entero(tr.w18)}</td>
                  <td className={td} />
                </tr>
              </tbody>
            </Tabla>
            {tr.filas.some((f) => f.origen_fc === 'dato') && (
              <p className="px-5 py-2 text-[12.5px] text-slate-500">* Factor camión dado (no calculado con los ejes de la fila).</p>
            )}
          </Tarjeta>

          {(() => {
            const top = [...tr.filas].sort((a, b) => b.w - a.w)[0]
            return top && (
              <Nota tipo="tip">
                «{top.nombre}» aporta el <strong>{num((100 * top.w) / tr.w18, 1)} %</strong> del W18. Los autos casi no
                cuentan aunque sean mayoría en el TPDA: el daño depende de la carga por eje, no de la cantidad de vehículos.
              </Nota>
            )
          })()}
        </>
      )}

      <Decisiones modulo="transito" />
      <Ecuaciones claves={['lef', 'crecimiento', 'esal']} />
    </div>
  )
}

// ------------------------------------------------------------------ tabla de vehículos
function TablaVehiculos({ nEjes }: { nEjes: number }) {
  const p = useProyecto()
  const t = p.transito
  const editar = useApp((s) => s.editar)
  const filas = useApp((s) => s.resultado?.transito?.filas)
  const u = t.unidad_carga
  const ev = (i: number, fn: (v: Vehiculo) => void) => editar((p) => fn(p.transito.vehiculos[i]))

  const setEje = (i: number, j: number, campo: 'tipo' | 'carga', valor: TipoEje | number | null) => ev(i, (v) => {
    const ejes: (Eje | null)[] = Array.from({ length: Math.max(v.ejes.length, j + 1) }, (_, k) => v.ejes[k] ?? null)
    const actual = ejes[j] ?? ['simple', 0]
    if (campo === 'tipo') ejes[j] = [valor as TipoEje, actual[1]]
    else if (valor == null || valor === 0) ejes[j] = ejes[j] ? [actual[0], 0] : null
    else ejes[j] = [actual[0], valor as number]
    // un eje sin carga y en la última posición se quita
    while (ejes.length && (ejes[ejes.length - 1] == null || ejes[ejes.length - 1]![1] === 0) && campo === 'carga') ejes.pop()
    v.ejes = ejes.map((e) => e ?? ['simple', 0]) as Eje[]
  })

  if (!t.vehiculos.length) {
    return <div className="px-5 py-10 text-center text-[14px] text-slate-500">Todavía no hay vehículos. Agregá el primero con el botón de abajo.</div>
  }

  return (
    <Tabla>
      <thead>
        <tr>
          <th className={cx(th, 'w-10 text-center')} rowSpan={2}>#</th>
          <th className={cx(th, 'min-w-52')} rowSpan={2}>Vehículo</th>
          <th className={cx(th, 'border-l border-slate-200 text-center')} colSpan={nEjes}>
            Cargas por eje ({u === 't' ? 'toneladas' : 'kip'})
          </th>
          <th className={cx(th, 'border-l border-slate-200 text-right')} rowSpan={2}>TPDA<br /><span className="font-normal normal-case">veh/día</span></th>
          <th className={cx(th, 'text-right')} rowSpan={2}>Tasa<br /><span className="font-normal normal-case">crec. %</span></th>
          <th className={cx(th, 'border-l border-slate-200 text-right')} rowSpan={2}>
            <span className="inline-flex items-center gap-1">Factor camión <Ayuda texto="Suma de los LEF de los ejes del vehículo: cuántos ejes de 18 kip equivale un pasaje. Se calcula solo. Si el enunciado o un pesaje te da el factor camión, usá «valor dado» y los ejes de esa fila se ignoran." /></span>
            <br /><span className="font-normal normal-case">Σ LEF</span>
          </th>
          <th className={cx(th, 'w-16')} rowSpan={2} />
        </tr>
        <tr>
          {Array.from({ length: nEjes }, (_, j) => (
            <th key={j} className={cx(th, 'border-l border-slate-200 text-center normal-case tracking-normal')}>{POSICION[j] ?? `Eje ${j + 1}`}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {t.vehiculos.map((v, i) => {
          const res = filas?.[i]
          const ejesRes = res && res.ejes.length === v.ejes.length ? res.ejes : null
          const conDato = v.factor_camion != null
          const faltan = res?.faltan ?? []
          const incompleta = faltan.length > 0
          return (
            <tr key={i} className={cx('group align-top', incompleta ? 'bg-amber-50/60' : 'hover:bg-slate-50/50')}>
              <td className={cx(td, 'pt-3 text-center')}>
                <div className="font-mono text-[12px] text-slate-400">{i + 1}</div>
                {res && (incompleta
                  ? <span title={`Falta: ${faltan.join(', ')}. Esta fila no suma al W18 hasta completarla.`}><CircleAlert className="mx-auto mt-1 h-4 w-4 text-amber-500" /></span>
                  : <span title="Fila completa: entra en el cálculo"><CheckCircle2 className="mx-auto mt-1 h-4 w-4 text-emerald-500" /></span>)}
              </td>
              <td className={td}>
                <input value={v.nombre} onChange={(e) => ev(i, (x) => { x.nombre = e.target.value })}
                  className="h-8 w-full rounded-md border border-transparent bg-transparent px-2 text-[13.5px] font-medium text-slate-800 hover:border-slate-200 focus:border-acento-500 focus:bg-white focus:outline-none" />
              </td>
              {Array.from({ length: nEjes }, (_, j) => {
                const eje = v.ejes[j]
                const er = ejesRes?.[j]
                const sinCarga = !conDato && !!eje && !(eje[1] > 0)
                return (
                  <td key={j} className={cx(td, 'border-l border-slate-100 px-2', conDato && 'opacity-40')}>
                    <div className="w-[108px] space-y-1">
                      <Numero compacto vacio valor={eje && eje[1] ? eje[1] : null} placeholder={sinCarga ? 'carga?' : '—'}
                        className={cx(sinCarga && 'rounded-lg ring-2 ring-amber-400')}
                        alCambiar={(x) => setEje(i, j, 'carga', x)} />
                      <Selector compacto valor={eje ? eje[0] : null} opciones={TIPOS} placeholder="—"
                        alCambiar={(x) => setEje(i, j, 'tipo', x)} />
                      <div className="h-4 whitespace-nowrap text-center font-mono text-[10.5px] tracking-tight text-slate-400" title="Carga con la que se entra a la tabla AASHTO → LEF leído">
                        {er && er.carga > 0 ? <>{num(er.carga_kip, 1)} kip → <span className="text-slate-700">{num(er.lef, 3)}</span></> : ''}
                      </div>
                    </div>
                  </td>
                )
              })}
              <td className={cx(td, 'border-l border-slate-100 px-2')}>
                <Numero compacto valor={v.tpda} dec={0} className={cx('w-20', !(v.tpda > 0) && 'rounded-lg ring-2 ring-amber-400')}
                  alCambiar={(x) => ev(i, (y) => { y.tpda = x ?? 0 })} />
              </td>
              <td className={cx(td, 'px-2')}>
                <Numero compacto valor={v.r * 100} dec={2} className="w-20" alCambiar={(x) => ev(i, (y) => { y.r = (x ?? 0) / 100 })} />
              </td>
              <td className={cx(td, 'border-l border-slate-100 px-2')}>
                <FactorCamion valor={v.factor_camion} calculado={res?.factor_camion}
                  alCambiar={(x) => ev(i, (y) => { y.factor_camion = x })} />
              </td>
              <td className={cx(td, 'px-1 pt-3')}>
                <div className="flex gap-0.5 opacity-0 transition group-hover:opacity-100">
                  <button title="Duplicar" onClick={() => editar((p) => { p.transito.vehiculos.splice(i + 1, 0, { ...structuredClone(v), nombre: `${v.nombre} (copia)` }) })}
                    className="grid h-7 w-7 place-items-center rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-700"><Copy className="h-3.5 w-3.5" /></button>
                  <button title="Borrar" onClick={() => editar((p) => { p.transito.vehiculos.splice(i, 1) })}
                    className="grid h-7 w-7 place-items-center rounded-md text-slate-400 hover:bg-red-50 hover:text-red-600"><Trash2 className="h-3.5 w-3.5" /></button>
                </div>
              </td>
            </tr>
          )
        })}
      </tbody>
    </Tabla>
  )
}

// ------------------------------------------------------------------ agregar vehículos
let cacheCatalogo: OpcionCatalogo[] | null = null

function AgregarVehiculo() {
  const editar = useApp((s) => s.editar)
  const [cat, setCat] = useState(cacheCatalogo)
  const [abierto, setAbierto] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { if (!cacheCatalogo) api.catalogo().then((c) => { cacheCatalogo = c.opciones; setCat(c.opciones) }) }, [])
  useEffect(() => {
    const cerrar = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false) }
    document.addEventListener('mousedown', cerrar)
    return () => document.removeEventListener('mousedown', cerrar)
  }, [])

  const agregar = (tipos: TipoEje[]) => {
    editar((p) => {
      p.transito.vehiculos.push({
        nombre: `Vehículo ${p.transito.vehiculos.length + 1}`, tpda: 0, r: 0, pesado: false, factor_camion: null,
        ejes: tipos.map((tp) => [tp, 0] as Eje),
      })
    })
    setAbierto(false)
  }

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setAbierto(!abierto)}
        className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-slate-900 px-3.5 text-[13.5px] font-medium text-white hover:bg-slate-800">
        <Plus className="h-4 w-4" /> Agregar vehículo <ChevronDown className="h-3.5 w-3.5 opacity-60" />
      </button>
      {abierto && (
        <div className="absolute bottom-11 left-0 z-30 w-72 rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl">
          <button onClick={() => agregar([])}
            className="w-full rounded-lg px-3 py-2 text-left text-[13.5px] font-medium text-slate-800 hover:bg-slate-50">Fila vacía</button>
          <div className="px-3 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Con disposición de ejes</div>
          {(cat ?? []).map((o) => (
            <button key={o.etiqueta} onClick={() => agregar(o.ejes.map(([tp]) => tp as TipoEje))}
              className="w-full rounded-lg px-3 py-1.5 text-left text-[13.5px] text-slate-700 hover:bg-slate-50">{o.etiqueta}</button>
          ))}
          <p className="border-t border-slate-100 px-3 py-2 text-[11.5px] text-slate-400">Las cargas, el TPDA y la tasa quedan para completar.</p>
        </div>
      )}
    </div>
  )
}

// ------------------------------------------------------------------ piezas chicas
/** Factor camión: muestra el Σ LEF calculado; opcionalmente se reemplaza por un valor dado. */
function FactorCamion({ valor, calculado, alCambiar }: {
  valor: number | null; calculado?: number; alCambiar: (v: number | null) => void
}) {
  const [abierto, setAbierto] = useState(false)
  if (valor == null && !abierto) {
    return (
      <div className="w-28 pt-1.5 text-right">
        <div className="font-mono text-[13.5px] font-semibold text-slate-900">{calculado != null ? num(calculado, 4) : '—'}</div>
        <button onClick={() => setAbierto(true)} className="mt-0.5 text-[11.5px] text-slate-400 underline decoration-dotted hover:text-acento-700">
          usar valor dado
        </button>
      </div>
    )
  }
  return (
    <div className="w-28 space-y-1">
      <Numero compacto vacio valor={valor} dec={4} placeholder="factor…" className="rounded-lg ring-2 ring-acento-300"
        alCambiar={alCambiar} />
      <div className="flex items-center justify-between text-[11px]">
        <span className="font-medium text-acento-700">valor dado</span>
        <button onClick={() => { alCambiar(null); setAbierto(false) }} className="text-slate-400 underline decoration-dotted hover:text-slate-700">
          volver a Σ LEF
        </button>
      </div>
    </div>
  )
}

/** Atajo (izquierda) + valor editable que entra al cálculo (derecha). */
function Grupo({ children }: { children: ReactNode }) {
  return <div className="-mt-2.5 grid grid-cols-[1.25fr_1fr] gap-2 rounded-xl bg-slate-50 p-2.5 ring-1 ring-slate-200/70">{children}</div>
}

function Pista({ children }: { children: ReactNode }) {
  return <p className="mt-1 text-[11.5px] leading-tight text-slate-500">{children}</p>
}

/** Resumen de qué filas entran al cálculo y cuáles esperan datos. */
function EstadoCarga() {
  const filas = useApp((s) => s.resultado?.transito?.filas)
  const resolviendo = useApp((s) => s.resolviendo)
  if (!filas) return null
  const incompletas = filas.map((f, i) => ({ ...f, n: i + 1 })).filter((f) => f.faltan.length)
  const ok = filas.length - incompletas.length
  return (
    <div className={cx('flex flex-wrap items-start gap-x-5 gap-y-1 border-t px-5 py-2.5 text-[13px]',
      incompletas.length ? 'border-amber-200 bg-amber-50 text-amber-900' : 'border-emerald-100 bg-emerald-50/70 text-emerald-900')}>
      <span className="inline-flex items-center gap-1.5 font-medium">
        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
        {ok} de {filas.length} vehículos entran en el cálculo{resolviendo ? ' · calculando…' : ''}
      </span>
      {incompletas.length > 0 && (
        <span className="inline-flex flex-wrap items-center gap-x-1.5">
          <CircleAlert className="h-4 w-4 text-amber-500" />
          Falta completar: {incompletas.map((f) => `fila ${f.n} (${f.faltan.join(', ')})`).join(' · ')}
        </span>
      )}
      <span className="ml-auto text-[12px] opacity-70">Cada cambio se recalcula al instante; el PDF y el Excel usan exactamente esta tabla.</span>
    </div>
  )
}
