import { ChevronDown, Copy, Plus, Table2, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import {
  Avisos, Ayuda, Barra, CampoNumero, CampoSelector, Concepto, Decisiones, Ecuaciones, Encabezado, Kpi, Kpis, Nota,
  Numero, Segmentado, Selector, Tabla, Tarjeta, cx, td, tdNum, th,
} from '../components/ui'
import { api, type OpcionCatalogo } from '../lib/api'
import { entero, g, num } from '../lib/formato'
import { useApp, useProyecto } from '../lib/store'
import type { Eje, TipoEje, Vehiculo } from '../lib/tipos'

const KIP_EXACTO = 2.20462
const KIP_CATEDRA = 2
const TIPOS: { valor: TipoEje; etiqueta: string }[] = [
  { valor: 'simple', etiqueta: 'Simple' },
  { valor: 'tandem', etiqueta: 'Tándem' },
  { valor: 'tridem', etiqueta: 'Trídem' },
]
const NOMBRE_TIPO: Record<TipoEje, string> = { simple: 'Simple', tandem: 'Tándem', tridem: 'Trídem' }
const POSICION = ['Eje delantero', 'Eje trasero 1', 'Eje trasero 2', 'Eje trasero 3', 'Eje trasero 4', 'Eje trasero 5']

const AYUDA = {
  n: 'Años de servicio que debe cubrir esta etapa. AASHTO recomienda 10–20 años para la etapa inicial.',
  fd: 'Fracción del tránsito total que va en la dirección más cargada. Normalmente 0,5 (rango 0,3–0,7).',
  fc: 'Fracción de los vehículos de esa dirección que circula por el carril de diseño: 1 carril → 1,0 · 2 carriles → 0,80–1,00 · 3 carriles → 0,60–0,80 · 4 o más → 0,50–0,75.',
  pt: 'Serviciabilidad terminal con la que se eligen las tablas LEF (2,0; 2,5 o 3,0). Conviene igualarla al pt de diseño.',
  sn: 'SN supuesto para leer los LEF (columna de la tabla). Se estima y luego se compara con el SN obtenido en el módulo 4.',
}

export default function Transito() {
  const p = useProyecto()
  const t = p.transito
  const editar = useApp((s) => s.editar)
  const tr = useApp((s) => s.resultado?.transito)
  const u = t.unidad_carga
  const nEjes = Math.max(4, ...t.vehiculos.map((v) => v.ejes.length))

  const cambiarUnidad = (nueva: 't' | 'kip') => editar((p) => {
    if (nueva === p.transito.unidad_carga) return
    const f = nueva === 'kip' ? p.transito.kip_por_t : 1 / p.transito.kip_por_t
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
          <li><strong>Factor de camión (FC):</strong> suma de los LEF de todos los ejes de un vehículo.</li>
          <li><strong>ESAL del año 1:</strong> TPDA × FC × 365 × F<sub>d</sub> × F<sub>c</sub> (solo el carril de diseño).</li>
          <li><strong>W<sub>18</sub>:</strong> ESAL acumulados en el período, con el crecimiento compuesto de cada vehículo.</li>
        </ul>
      </Concepto>

      <Tarjeta titulo="Parámetros del tránsito">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <CampoNumero etiqueta="Período n (años)" ayuda={AYUDA.n} valor={t.n} dec={0} min={1} max={50}
            alCambiar={(v) => editar((p) => { p.transito.n = v ?? 0 })} />
          <CampoNumero etiqueta="Distribución direccional Fd" ayuda={AYUDA.fd} valor={t.fd} min={0.1} max={1}
            alCambiar={(v) => editar((p) => { p.transito.fd = v ?? 0 })} />
          <CampoNumero etiqueta="Distribución por carril Fc" ayuda={AYUDA.fc} valor={t.fc} min={0.1} max={1}
            alCambiar={(v) => editar((p) => { p.transito.fc = v ?? 0 })} />
          <CampoSelector etiqueta="pt de las tablas LEF" ayuda={AYUDA.pt} valor={t.pt}
            opciones={[2, 2.5, 3].map((x) => ({ valor: x, etiqueta: num(x, 1) }))}
            alCambiar={(v) => editar((p) => { p.transito.pt = v })} />
          <CampoNumero etiqueta="SN supuesto (LEF)" ayuda={AYUDA.sn} valor={t.sn_lef} dec={1} min={1} max={6}
            alCambiar={(v) => editar((p) => { p.transito.sn_lef = v ?? 3 })} />
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
            {u === 't' && (
              <div className="flex items-center gap-2 text-[13px] text-slate-500">
                1 t =
                <Segmentado valor={Math.abs(t.kip_por_t - KIP_CATEDRA) < 1e-9 ? KIP_CATEDRA : KIP_EXACTO}
                  alCambiar={(v) => editar((p) => { p.transito.kip_por_t = v })}
                  opciones={[{ valor: KIP_EXACTO, etiqueta: '2,2046 kip (exacta)' }, { valor: KIP_CATEDRA, etiqueta: '2 kip (cátedra)' }]} />
                <Ayuda texto="Las tablas LEF están en kip. La conversión exacta es 1 t = 1000 kg = 2204,6 lb = 2,2046 kip. En clase se usa ×2 para leer las tablas a mano; el Práctico 3 está resuelto así." />
              </div>
            )}
          </div>
        }>
        <TablaVehiculos nEjes={nEjes} />
        <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 px-5 py-3">
          <AgregarVehiculo />
          <span className="ml-auto text-[12.5px] text-slate-500">
            En cada eje: carga arriba, tipo abajo; debajo se ve la carga en kip y el LEF leído. «—» = el vehículo no tiene ese eje.
          </span>
        </div>
      </Tarjeta>

      <Avisos modulo="transito" />

      {tr && (
        <>
          <Kpis>
            <Kpi destacado etiqueta="W18 de diseño" valor={entero(tr.w18)} sub={`ESAL en ${g(tr.n)} años, carril de diseño`} />
            <Kpi etiqueta="ESAL del primer año" valor={entero(tr.esal1_total)} sub="carril de diseño" />
            <Kpi etiqueta="TPDA total" valor={entero(tr.tpda_total)} sub="veh/día, ambos sentidos" />
            <Kpi etiqueta="Factores" valor={`${g(tr.fd)} × ${g(tr.fc)}`} sub="Fd × Fc" />
          </Kpis>

          <Tarjeta titulo="Ejes equivalentes por vehículo" pad={false}
            sub="G = factor de crecimiento compuesto · ESAL año 1 = TPDA × FC × 365 × Fd × Fc · W = ESAL año 1 × G">
            <Tabla>
              <thead>
                <tr>
                  <th className={th}>Vehículo</th>
                  <th className={cx(th, 'text-right')}>TPDA</th>
                  <th className={cx(th, 'text-right')}>r</th>
                  <th className={cx(th, 'text-right')}>FC</th>
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
              <p className="px-5 py-2 text-[12.5px] text-slate-500">* Factor de camión ingresado como dato.</p>
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
    return <div className="px-5 py-10 text-center text-[14px] text-slate-500">Todavía no hay vehículos. Agregá uno o cargá la tabla del Práctico 3.</div>
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
            <span className="inline-flex items-center gap-1">FC <Ayuda texto="Factor de camión = Σ LEF de los ejes. Si conocés el factor (pesaje o enunciado), escribilo y se ignoran los ejes de esa fila." /></span>
            <br /><span className="font-normal normal-case">Σ LEF / dato</span>
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
          return (
            <tr key={i} className="group align-top hover:bg-slate-50/50">
              <td className={cx(td, 'pt-3.5 text-center font-mono text-[12px] text-slate-400')}>{i + 1}</td>
              <td className={td}>
                <input value={v.nombre} onChange={(e) => ev(i, (x) => { x.nombre = e.target.value })}
                  className="h-8 w-full rounded-md border border-transparent bg-transparent px-2 text-[13.5px] font-medium text-slate-800 hover:border-slate-200 focus:border-acento-500 focus:bg-white focus:outline-none" />
              </td>
              {Array.from({ length: nEjes }, (_, j) => {
                const eje = v.ejes[j]
                const er = ejesRes?.[j]
                return (
                  <td key={j} className={cx(td, 'border-l border-slate-100 px-2', conDato && 'opacity-40')}>
                    <div className="w-[108px] space-y-1">
                      <Numero compacto vacio valor={eje && eje[1] ? eje[1] : null} placeholder="—"
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
                <Numero compacto valor={v.tpda} dec={0} className="w-20" alCambiar={(x) => ev(i, (y) => { y.tpda = x ?? 0 })} />
              </td>
              <td className={cx(td, 'px-2')}>
                <Numero compacto valor={v.r * 100} dec={2} className="w-20" alCambiar={(x) => ev(i, (y) => { y.r = (x ?? 0) / 100 })} />
              </td>
              <td className={cx(td, 'border-l border-slate-100 px-2')}>
                <div className="w-24 space-y-1">
                  <Numero compacto vacio valor={v.factor_camion} dec={4} placeholder="dato…"
                    alCambiar={(x) => ev(i, (y) => { y.factor_camion = x })} />
                  <div className="text-right font-mono text-[12px] text-slate-600">
                    {res ? <>{conDato ? 'dato' : 'Σ'} = <b className="text-slate-900">{num(res.factor_camion, 4)}</b></> : ''}
                  </div>
                </div>
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
let cacheCatalogo: { fuente: string; opciones: OpcionCatalogo[] } | null = null

function AgregarVehiculo() {
  const editar = useApp((s) => s.editar)
  const [cat, setCat] = useState(cacheCatalogo)
  const [abierto, setAbierto] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { if (!cacheCatalogo) api.catalogo().then((c) => { cacheCatalogo = c; setCat(c) }) }, [])
  useEffect(() => {
    const cerrar = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false) }
    document.addEventListener('mousedown', cerrar)
    return () => document.removeEventListener('mousedown', cerrar)
  }, [])

  const agregar = (ops: OpcionCatalogo[]) => {
    editar((p) => {
      const f = p.transito.unidad_carga === 'kip' ? p.transito.kip_por_t : 1
      for (const o of ops) {
        p.transito.vehiculos.push({
          nombre: o.nombre, tpda: 0, r: 0, pesado: o.pesado, factor_camion: null,
          ejes: o.ejes.map(([tp, c]) => [tp as TipoEje, Math.round(c * (o.unidad === 't' ? f : 1) * 1000) / 1000]),
        })
      }
    })
    setAbierto(false)
  }
  const practico = cat?.opciones.filter((o) => o.fuente) ?? []
  const configs = cat?.opciones.filter((o) => !o.fuente) ?? []

  return (
    <div ref={ref} className="relative flex items-center gap-2">
      <button onClick={() => setAbierto(!abierto)}
        className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-slate-900 px-3.5 text-[13.5px] font-medium text-white hover:bg-slate-800">
        <Plus className="h-4 w-4" /> Agregar vehículo <ChevronDown className="h-3.5 w-3.5 opacity-60" />
      </button>
      <button onClick={() => agregar(practico)} disabled={!practico.length}
        className="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-[13.5px] font-medium text-slate-600 ring-1 ring-slate-300 hover:bg-slate-50">
        <Table2 className="h-4 w-4" /> Cargar la tabla del Práctico 3
      </button>
      {abierto && (
        <div className="absolute bottom-11 left-0 z-30 max-h-[70vh] w-[460px] overflow-y-auto rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl">
          <button onClick={() => agregar([{ etiqueta: '', nombre: 'Vehículo', pesado: false, ejes: [], unidad: null, fuente: null }])}
            className="w-full rounded-lg px-3 py-2 text-left text-[13.5px] font-medium text-slate-800 hover:bg-slate-50">Fila vacía</button>
          <div className="px-3 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Tabla del Práctico 3 (cátedra) · con cargas</div>
          {practico.map((o) => (
            <button key={o.etiqueta} onClick={() => agregar([o])} className="flex w-full items-baseline justify-between gap-3 rounded-lg px-3 py-1.5 text-left hover:bg-slate-50">
              <span className="text-[13.5px] text-slate-800">{o.nombre}</span>
              <span className="font-mono text-[11.5px] text-slate-500">{o.ejes.map(([tp, c]) => `${NOMBRE_TIPO[tp as TipoEje].toLowerCase()} ${g(c)}`).join(' + ')} t</span>
            </button>
          ))}
          <div className="px-3 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Solo configuración de ejes · cargas a completar</div>
          {configs.map((o) => (
            <button key={o.etiqueta} onClick={() => agregar([o])} className="w-full rounded-lg px-3 py-1.5 text-left text-[13.5px] text-slate-700 hover:bg-slate-50">
              {o.etiqueta.replace(/^⚙️ /, '').replace(' · cargas a completar', '')}
            </button>
          ))}
          {cat && <p className="border-t border-slate-100 px-3 py-2 text-[11.5px] text-slate-400">Fuente de las cargas: {cat.fuente}. TPDA y r quedan en cero para completar.</p>}
        </div>
      )}
    </div>
  )
}
