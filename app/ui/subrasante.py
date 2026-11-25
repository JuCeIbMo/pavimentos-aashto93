"""Módulo 2 — Módulo resiliente efectivo de la subrasante y daño relativo."""

import altair as alt
import pandas as pd
import streamlit as st

from pavimentos.formato import entero, num
from pavimentos.modelo import Periodo

from .componentes import avisos, concepto, decisiones, ecuacion, encabezado, fila_metricas, seccion
from .estado import k, proyecto

CONCEPTO = """
La subrasante no tiene la misma rigidez todo el año: en épocas de lluvia o de deshielo se
**ablanda** (M<sub>R</sub> bajo) y en épocas secas o congelada se **rigidiza** (M<sub>R</sub> alto).

No alcanza con promediar los M<sub>R</sub>, porque el daño **no es lineal**: un mes débil daña
mucho más de lo que un mes rígido "compensa". AASHTO calcula el **daño relativo u<sub>f</sub>** de cada
período, lo promedia ponderando por su duración y busca el M<sub>R</sub> constante que produciría ese
mismo daño. Ese es el **M<sub>R</sub> efectivo**, siempre menor que el promedio aritmético.

Si solo tenés CBR, el programa estima M<sub>R</sub> con las correlaciones de la guía. Si tenés ensayos
triaxiales (AASHTO T-307), cargá el M<sub>R</sub> directamente.
"""

COLUMNAS = {
    "nombre": st.column_config.TextColumn("Período", width="medium"),
    "meses": st.column_config.NumberColumn("Duración (meses)", min_value=0.0, max_value=12.0, step=0.5, format="%.1f",
                                           help="Podés usar medios meses (quincenas). Deben sumar 12."),
    "cbr": st.column_config.NumberColumn("CBR (%)", min_value=0.0, max_value=20.0, format="%.2f",
                                         help="Correlación válida hasta CBR 20 %."),
    "mr": st.column_config.NumberColumn("M_R directo (psi)", min_value=0.0, format="%.0f",
                                        help="Opcional: si lo cargás, tiene prioridad sobre el CBR."),
}


def _df(periodos):
    return pd.DataFrame([{"nombre": x.nombre, "meses": x.meses, "cbr": x.cbr, "mr": x.mr} for x in periodos],
                        columns=list(COLUMNAS))


def _f(x):
    return None if x is None or pd.isna(x) else float(x)


def render(res: dict):
    p = proyecto()
    encabezado("Módulo resiliente efectivo de la subrasante",
               "Variación estacional de la subrasante, daño relativo y M_R de diseño.", badge="02")
    concepto("¿Por qué un M_R «efectivo» y no el promedio?", CONCEPTO)

    seccion("Variación estacional", "Un renglón por período (mes, quincena o estación).")
    fuente = st.session_state.setdefault(k("per_df"), _df(p.subrasante.periodos))
    editado = st.data_editor(fuente, num_rows="dynamic", width="stretch", hide_index=True,
                             column_config=COLUMNAS, key=k("per_editor"))
    periodos = []
    for _, f in editado.iterrows():
        if pd.isna(f.get("meses")) and _f(f.get("cbr")) is None and _f(f.get("mr")) is None:
            continue
        periodos.append(Periodo(nombre=str(f.get("nombre") or "Período"), meses=_f(f.get("meses")) or 0.0,
                                cbr=_f(f.get("cbr")), mr=_f(f.get("mr"))))
    p.subrasante.periodos = periodos
    suma = sum(x.meses for x in periodos)
    st.caption(f"Meses cargados: **{num(suma, 1)} / 12**")

    avisos(res, "subrasante")
    sub = res.get("subrasante")
    if not sub:
        return

    seccion("Resultados")
    fila_metricas([
        {"etiqueta": "M_R efectivo", "valor": f"{entero(sub['mr_efectivo'])} psi",
         "sub": f"≈ {num(sub['mr_efectivo'] / 14.2233, 0)} kg/cm²"},
        {"etiqueta": "Daño relativo promedio ū_f", "valor": num(sub["uf_bar"], 4), "sub": "ponderado por duración"},
        {"etiqueta": "Promedio aritmético de M_R", "valor": f"{entero(sub['mr_promedio'])} psi",
         "sub": "no se usa: sobreestima el soporte"},
    ])
    df = pd.DataFrame([{"Período": f["nombre"], "Meses": f["meses"], "CBR (%)": f["cbr"], "M_R (psi)": f["mr"],
                        "Origen M_R": f["origen"], "u_f": f["uf"], "u_f · meses": f["uf_meses"],
                        "% del daño anual": 100 * f["uf_meses"] / sub["suma_uf"]} for f in sub["filas"]])
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.dataframe(df, hide_index=True, width="stretch", column_config={
            "M_R (psi)": st.column_config.NumberColumn(format="%.0f"),
            "u_f": st.column_config.NumberColumn(format="%.4f"),
            "u_f · meses": st.column_config.NumberColumn(format="%.4f"),
            "% del daño anual": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
        })
    with c2:
        chart = alt.Chart(df).mark_bar(color="#C98A00").encode(
            x=alt.X("Período:N", sort=None, title=None),
            y=alt.Y("% del daño anual:Q", title="% del daño anual"),
            tooltip=["Período", "M_R (psi)", alt.Tooltip("% del daño anual:Q", format=".1f")],
        ).properties(height=230)
        st.altair_chart(chart, use_container_width=True)
    peor = max(sub["filas"], key=lambda f: f["uf_meses"])
    st.caption(f"💡 «{peor['nombre']}» concentra el {num(100 * peor['uf_meses'] / sub['suma_uf'], 0)} % del daño "
               f"anual con {num(100 * peor['meses'] / 12, 0)} % del tiempo: por eso drenar bien la subrasante rinde tanto.")
    decisiones(res, "subrasante")

    with st.expander("📐 Procedimiento y ecuaciones"):
        ecuacion("mr_cbr")
        ecuacion("danio")
        ecuacion("mr_ef")
