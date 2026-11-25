// Memoria de cálculo — Pavimento flexible AASHTO 93
// Los datos llegan ya formateados en datos.json (generado por exportar_pdf.py).

#let d = json("datos.json")
#let acento = rgb("#C98A00")
#let oscuro = rgb("#1F2937")
#let suave = rgb("#F3F4F6")
#let linea = rgb("#D1D5DB")
#let verde = rgb("#15803D")
#let rojo = rgb("#B91C1C")

#set document(title: d.titulo, author: if d.autor != "" { d.autor } else { "Pavimentos AASHTO 93" })
#set text(lang: "es", font: "Libertinus Serif", size: 10.5pt, fill: oscuro)
#set par(justify: true, leading: 0.62em)
#set page(
  paper: "a4",
  margin: (x: 2.2cm, top: 2.4cm, bottom: 2.2cm),
  header: context {
    if counter(page).get().first() > 1 [
      #set text(size: 8pt, fill: luma(110))
      #d.titulo #h(1fr) Memoria de cálculo · AASHTO 93
      #v(-6pt)
      #line(length: 100%, stroke: 0.4pt + linea)
    ]
  },
  footer: context [
    #set text(size: 8pt, fill: luma(110))
    Generado con el paquete computacional «Pavimentos AASHTO 93» · #d.fecha
    #h(1fr) Página #counter(page).display() de #counter(page).final().first()
  ],
)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => block(above: 1.4em, below: 0.8em, text(size: 13pt, weight: "bold")[
  #box(width: 4pt, height: 11pt, fill: acento, baseline: 1pt)#h(7pt)#if it.numbering != none [#counter(heading).display(it.numbering)#h(6pt)]#it.body
])
#show heading.where(level: 2): it => block(above: 1.1em, below: 0.6em, text(size: 11pt, weight: "bold")[
  #if it.numbering != none [#counter(heading).display(it.numbering)#h(5pt)]#it.body
])
#set math.equation(numbering: none)
#show math.equation.where(block: true): it => block(width: 100%, inset: (y: 4pt), it)

// ---------- utilidades ----------
#let tabla(cols, enc, filas, alinear: none) = {
  let n = enc.len()
  table(
    columns: cols,
    stroke: (x, y) => (bottom: if y == 0 { 0.8pt + oscuro } else { 0.3pt + linea }),
    fill: (x, y) => if y == 0 { suave },
    inset: (x: 5pt, y: 4pt),
    align: if alinear == none { (x, y) => if x == 0 { left } else { right } } else { alinear },
    table.header(..enc.map(e => text(size: 8.5pt, weight: "bold", e))),
    ..filas.flatten().map(c => text(size: 8.5pt, c)),
  )
}
#let par_dato(k, v) = (text(fill: luma(90), k), strong(v))
#let datos(pares) = grid(
  columns: (auto, 1fr, auto, 1fr), column-gutter: 10pt, row-gutter: 7pt,
  ..pares.map(p => par_dato(p.at(0), p.at(1))).flatten(),
)
#let fuente(t) = block(above: 2pt, below: 8pt, text(size: 8pt, fill: luma(110), style: "italic", [Fuente: #t]))
#let nota(t) = block(fill: suave, inset: 8pt, radius: 3pt, width: 100%, text(size: 9pt, t))

// ---------- portada ----------
#block(width: 100%, inset: (y: 4pt))[
  #text(size: 9pt, fill: acento, weight: "bold", tracking: 1.5pt)[MEMORIA DE CÁLCULO · PAVIMENTO FLEXIBLE]
  #v(2pt)
  #text(size: 20pt, weight: "bold")[#d.titulo]
  #v(-4pt)
  #text(size: 10pt, fill: luma(90))[Diseño estructural por el método AASHTO 1993]
]
#line(length: 100%, stroke: 1.2pt + acento)
#grid(columns: (1fr, 1fr, 1fr), column-gutter: 8pt,
  [#text(size: 8pt, fill: luma(110))[Autor] \ #(if d.autor != "" { d.autor } else { "—" })],
  [#text(size: 8pt, fill: luma(110))[Ubicación] \ #(if d.ubicacion != "" { d.ubicacion } else { "—" })],
  [#text(size: 8pt, fill: luma(110))[Fecha] \ #d.fecha],
)
#if d.descripcion != "" [ #v(4pt) #text(size: 9.5pt, d.descripcion) ]

// ---------- resumen ----------
#if "capas" in d {
  let c = d.capas
  v(8pt)
  block(stroke: 0.8pt + linea, radius: 4pt, inset: 12pt, width: 100%)[
    #grid(columns: (1.1fr, 1fr), column-gutter: 16pt,
      [
        #text(size: 9pt, fill: acento, weight: "bold", tracking: 1pt)[RESULTADO]
        #v(2pt)
        #let maxcm = calc.max(..c.dib.map(x => x.cm), 1)
        #let total = c.dib.map(x => x.cm).sum()
        #let escala = 4.2cm / calc.max(total, 1)
        #let colores = (rgb("#374151"), rgb("#D6B46B"), rgb("#E8DCC0"))
        #for (i, capa) in c.dib.enumerate() {
          if capa.cm > 0 {
            grid(columns: (2.6cm, 1fr), column-gutter: 6pt,
              rect(width: 100%, height: calc.max(capa.cm * escala, 10pt), fill: colores.at(i), stroke: 0.4pt + oscuro,
                align(center + horizon, text(size: 8pt, weight: "bold", fill: if i == 0 { white } else { oscuro }, capa.txt))),
              align(horizon, text(size: 8.5pt, capa.nombre)),
            )
            v(-5pt)
          }
        }
        #grid(columns: (2.6cm, 1fr), column-gutter: 6pt,
          rect(width: 100%, height: 14pt, fill: tiling(size: (5pt, 5pt), place(line(start: (0%, 100%), end: (100%, 0%), stroke: 0.4pt + luma(140)))), stroke: 0.4pt + oscuro),
          align(horizon, text(size: 8.5pt)[Subrasante · M#sub[R] = #d.diseno.mr psi]),
        )
      ],
      [
        #set text(size: 9.5pt)
        #grid(columns: (1fr, auto), row-gutter: 7pt,
          [Tránsito de diseño W#sub[18]], strong(d.diseno.w18),
          [M#sub[R] efectivo], strong(d.diseno.mr + " psi"),
          [Confiabilidad R / Z#sub[R]], strong(d.diseno.r + " / " + d.diseno.zr),
          [SN requerido], strong(d.diseno.sn_req),
          [SN adoptado], strong(d.diseno.sn_adop),
          [SN aportado], strong(c.total),
          [Espesor total], strong(c.espesor_total + " " + c.unidad),
          ..(if "clima" in d { ([Período de desempeño], strong(d.clima.periodo + " años")) } else { () }),
        )
        #v(6pt)
        #if c.cumple and d.ok {
          box(fill: verde.lighten(85%), inset: 6pt, radius: 3pt, text(fill: verde, weight: "bold")[✓ La estructura cumple las verificaciones de SN])
        } else {
          box(fill: rojo.lighten(85%), inset: 6pt, radius: 3pt, text(fill: rojo, weight: "bold")[✗ Revisar: hay verificaciones o datos con error])
        }
      ],
    )
  ]
}

#if d.avisos.len() > 0 {
  v(6pt)
  nota[
    *Avisos del programa* \
    #for a in d.avisos [
      #let col = if a.nivel == "error" { rojo } else if a.nivel == "warn" { acento } else { luma(100) }
      #text(fill: col, weight: "bold")[#(if a.nivel == "error" { "Error" } else if a.nivel == "warn" { "Atención" } else { "Nota" }):] #a.texto \
    ]
  ]
}

// ---------- 1. Tránsito ----------
#if "transito" in d {
  let t = d.transito
  [= Tránsito: ejes equivalentes (módulo 1)]
  datos((
    ([Período de diseño n], t.n + " años"), ([Distribución direccional F#sub[d]], t.fd),
    ([Distribución por carril F#sub[c]], t.fc), ([p#sub[t] / SN para LEF], t.pt + " / " + t.sn),
    ([TPDA total], t.tpda + " veh/día"), ([Vehículos pesados], t.pesados),
  ))
  [
    $ G = ((1+r)^n - 1) / r #h(2em) W_18 = sum_i "TPDA"_i dot "FC"_i dot 365 dot F_d dot F_c dot G_i $
  ]
  fuente[AASHTO (1993), Parte II, sec. 2.1.2 y Apéndice D (LEF, tablas D.1–D.9).]
  tabla((2fr, 0.8fr, 0.7fr, 1fr, 0.8fr, 1.1fr, 1.3fr),
    ("Vehículo", "TPDA", "r", "FC", "G", "ESAL año 1", "W (n años)"), t.filas)
  if t.hay_dato [ #text(size: 8pt)[\* Factor de camión ingresado como dato (estudio de pesaje o fuente).] ]
  [
    #v(4pt)
    *Tránsito de diseño acumulado: W#sub[18] = #t.w18 ESAL* (ESAL del primer año: #t.esal1).
  ]
  if t.ejes.len() > 0 {
    [== Factores de equivalencia por eje]
    tabla((2fr, 1fr, 1fr, 1fr, 1fr), ("Vehículo", "Tipo de eje", "Carga (t)", "Carga (kip)", "LEF"), t.ejes)
    fuente[AASHTO (1993), Apéndice D. Interpolación bilineal en carga y SN.]
  }
}

// ---------- 2. Subrasante ----------
#if "subrasante" in d {
  let s = d.subrasante
  [= Módulo resiliente efectivo de la subrasante (módulo 2)]
  [
    $ u_f = 1.18 times 10^8 dot M_R^(-2.32) #h(2em) overline(u)_f = (sum u_(f,i) dot t_i) / 12 #h(2em) M_(R,"ef") = (overline(u)_f / (1.18 times 10^8))^(-1 \/ 2.32) $
  ]
  fuente[AASHTO (1993), Parte II, sec. 2.3.1 y fig. 2.3. Correlación CBR–M#sub[R]: AASHTO (1993), Parte II, sec. 1.5.]
  tabla((2fr, 0.7fr, 0.7fr, 1fr, 1.3fr, 0.9fr, 1fr),
    ("Período", "Meses", "CBR (%)", "M_R (psi)", "Origen M_R", "u_f", "u_f · meses"), s.filas)
  [
    #v(4pt)
    $sum u_f dot t$ = #s.suma → $overline(u)_f$ = #s.uf_bar → *M#sub[R] efectivo = #s.mr_ef psi* (el promedio aritmético sería #s.mr_prom psi).
  ]
}

// ---------- 3. Diseño ----------
#if "diseno" in d {
  let g = d.diseno
  [= Diseño estructural (módulo 4)]
  [== Parámetros de diseño]
  datos((
    ([W#sub[18] de diseño], g.w18), ([Origen], g.fuente_w18),
    ([M#sub[R] efectivo], g.mr + " psi"), ([Origen], g.fuente_mr),
    ([Confiabilidad R], g.r), ([Etapas / R por etapa], g.etapas + " / " + g.r_etapa),
    ([Z#sub[R]], g.zr), ([S#sub[o]], g.so),
    ([p#sub[0] / p#sub[t]], g.p0 + " / " + g.pt), ([ΔPSI], g.dpsi),
  ))
  [
    $ log W_18 = Z_R S_o + 9.36 log("SN"+1) - 0.20 + (log(Delta "PSI" \/ (4.2 - 1.5))) / (0.40 + 1094 \/ ("SN"+1)^5.19) + 2.32 log M_R - 8.07 $
  ]
  fuente[AASHTO (1993), Parte II, ec. 3.1 (nomograma fig. 3.1). Se resuelve para SN por bisección.]
  [Resolviendo la ecuación con los parámetros anteriores: *SN requerido = #g.sn_req*, SN adoptado = *#g.sn_adop*.]

  [== Materiales y coeficientes estructurales]
  tabla((1.6fr, 1fr, 1.6fr, 0.8fr, 1.9fr, 0.5fr),
    ("Capa", "E (psi)", "Origen E", "a", "Origen a", "m"), g.materiales)
  fuente[Coeficientes: AASHTO (1993), Parte II, figs. 2.5–2.7; correlaciones de Cabezas (2006), §4.10–4.11.]
}

// ---------- 4. Clima ----------
#if "clima" in d {
  let c = d.clima
  [= Ajuste por condiciones ambientales (módulo 6)]
  [
    $ Delta "PSI"_"SW" = 0.00335 dot V_R dot P_S dot (1 - e^(-theta t)) $
    #if c.helada [ $ Delta "PSI"_"FH" = 0.01 dot P_F dot Delta "PSI"_"MAX" dot (1 - e^(-0.02 phi t)) $ ]
  ]
  fuente[AASHTO (1993), Apéndice G, ec. G.4 y G.8; Parte II, sec. 3.1.4.]
  datos((([V#sub[R]], c.vr + " pulg"), ([P#sub[S]], c.ps), ([θ], c.theta), ([Período objetivo], c.objetivo + " años")))
  v(4pt)
  tabla((1fr, 1fr, 1fr, 1fr, 1.4fr, 1fr),
    ("t supuesto", "ΔPSI_SW", "ΔPSI_FH", "ΔPSI_TR", "W admisible", "t calculado"), c.iter)
  [
    #v(4pt)
    Se converge cuando el período supuesto y el calculado difieren menos de 1 año.
    *Período de desempeño = #c.periodo años*; W admisible = #c.w_adm ESAL con ΔPSI#sub[TR] = #c.dpsi_tr.
  ]
}

// ---------- 5. Capas ----------
#if "capas" in d {
  let c = d.capas
  [= Espesores de capa]
  [
    $ D_1 >= "SN"_1 / a_1 #h(1.5em) D_2 >= ("SN"_2 - a_1 D_1^*) / (a_2 m_2) #h(1.5em) D_3 >= ("SN"_3 - a_1 D_1^* - a_2 m_2 D_2^*) / (a_3 m_3) $
  ]
  fuente[AASHTO (1993), Parte II, fig. 3.2 (diseño por capas) y ec. 3.2.]
  [Cada capa se dimensiona para proteger a la de abajo: SN#sub[1] con E de la base, SN#sub[2] con E de la subbase y SN#sub[3] con M#sub[R]. Tránsito usado: W = #c.w, ΔPSI = #c.dpsi. Mínimos: #c.minimos.]
  v(4pt)
  tabla((1.6fr, 0.8fr, 0.6fr, 0.9fr, 1fr, 1fr, 1fr, 0.9fr),
    ("Capa", "a", "m", "SN req.", "D calc. (" + c.unidad + ")", "D adopt. (" + c.unidad + ")", "D (" + c.otra_unidad + ")", "SN aporte"), c.filas)
  [== Verificaciones]
  tabla((3fr, 1fr, 1fr, 1fr), ("Criterio", "Aportado", "Requerido", "Estado"), c.verif)
}

// ---------- 6. Sensibilidad ----------
#if "tornado" in d {
  [= Análisis de sensibilidad]
  [Se varía cada parámetro ±20 % (en R se varía la probabilidad de falla 100 − R) manteniendo el resto fijo, y se recalcula todo el diseño. La variable más influyente en este proyecto es *#d.tornado_top*.]
  figure(image("tornado.png", width: 92%), caption: [Diagrama tornado del SN requerido.])
  tabla((2.2fr, 1fr, 1fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr),
    ("Variable", "Valor −", "Valor +", "SN −", "SN +", "Esp. −", "Esp. +"), d.tornado)
  figure(image("curva_mr.png", width: 92%), caption: [SN requerido y espesor total frente al M#sub[R] de la subrasante (línea punteada: valor del proyecto).])
}

// ---------- 7. Decisiones ----------
#if d.decisiones.len() > 0 {
  [= Decisiones de diseño]
  for x in d.decisiones [ - #x ]
}

// ---------- 8. Referencias ----------
= Referencias bibliográficas
#set par(hanging-indent: 1.2em, justify: false)
#for r in d.referencias [ #text(size: 9pt, r) \ #v(2pt) ]
