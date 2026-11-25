"""Análisis de sensibilidad y comparación de escenarios."""

import math

import altair as alt
import pandas as pd
import streamlit as st

from pavimentos.formato import auto, entero, num
from pavimentos.sensibilidad import VARIABLES, barrido, comparar_escenarios, rango_por_defecto, tornado, valor_actual

from .componentes import concepto, encabezado, seccion
from .estado import k, proyecto

CONCEPTO = """
Un diseño no es un número: es la respuesta a un conjunto de supuestos. Esta página muestra
**qué pasa si un supuesto cambia** y **cuál pesa más**.

- **Curva:** se mueve una variable en todo su rango y se recalcula el diseño completo (con los mismos
  mínimos y redondeos). El SN varía de forma continua; el espesor total, en escalones, por el redondeo.
- **Tornado:** cada variable se mueve ±X % desde el valor del proyecto. Las barras más largas son las
  variables a las que el diseño es más sensible: conviene medirlas mejor (por ejemplo, más ensayos de
  M<sub>R</sub> o un mejor conteo de tránsito).
- **Escenarios:** alternativas completas lado a lado (otra confiabilidad, un drenaje mejor, una subrasante
  mejorada…), para decidir con números.
"""


def _curva(p):
    c = st.columns([1.2, 1, 1])
    clave = c[0].selectbox("Variable", list(VARIABLES), format_func=lambda x: VARIABLES[x].etiqueta, key=k("s_var"))
    var = VARIABLES[clave]
    valores = rango_por_defecto(p, clave, 31)
    lo, hi = c[1].number_input("Desde", value=float(valores[0]), key=k(f"s_lo_{clave}")), \
        c[2].number_input("Hasta", value=float(valores[-1]), key=k(f"s_hi_{clave}"))
    if hi <= lo:
        st.warning("«Hasta» debe ser mayor que «Desde».")
        return
    n = 31
    if clave == "w18":
        a, b = math.log10(lo), math.log10(hi)
        xs = [10 ** (a + (b - a) * i / (n - 1)) for i in range(n)]
    else:
        xs = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    pts = [x for x in barrido(p, clave, xs) if x.get("sn_requerido") is not None]
    if not pts:
        st.info("No se pudo resolver el diseño en ese rango.")
        return
    x0 = valor_actual(p, clave)
    df = pd.DataFrame(pts)
    unidad = pts[0]["unidad"]
    escala = alt.Scale(type="log") if clave == "w18" else alt.Scale(zero=False)
    base = alt.Chart(df).encode(x=alt.X("x:Q", title=f"{var.etiqueta} ({var.unidad})", scale=escala))
    sn = base.mark_line(color="#1F2937", strokeWidth=2.5).encode(
        y=alt.Y("sn_requerido:Q", title="SN requerido", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("x:Q", format=",.3~f"), alt.Tooltip("sn_requerido:Q", format=".3f")])
    esp = base.mark_line(color="#C98A00", interpolate="step-after").encode(
        y=alt.Y("espesor_total:Q", title=f"Espesor total ({unidad})", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("x:Q", format=",.3~f"), "espesor_total:Q", "d1:Q", "d2:Q", "d3:Q"])
    capas = []
    regla = alt.Chart(pd.DataFrame({"x": [x0]})).mark_rule(strokeDash=[4, 3], color="#6B7280").encode(x="x:Q")
    st.altair_chart(alt.layer(sn, esp, regla).resolve_scale(y="independent").properties(height=320),
                    use_container_width=True)
    st.caption(f"Línea negra: SN requerido · línea ámbar: espesor total · punteada: valor actual ({auto(x0)}). "
               f"{var.explicacion}")
    for f in pts:
        capas += [{"x": f["x"], "Capa": "1 · Carpeta", "Espesor": f["d1"]},
                  {"x": f["x"], "Capa": "2 · Base", "Espesor": f["d2"]},
                  {"x": f["x"], "Capa": "3 · Subbase", "Espesor": f["d3"]}]
    with st.expander("Ver cómo se reparte el espesor entre capas"):
        ch = alt.Chart(pd.DataFrame(capas)).mark_area(interpolate="step-after").encode(
            x=alt.X("x:Q", title=var.etiqueta, scale=escala),
            y=alt.Y("Espesor:Q", stack=True, title=f"Espesor ({unidad})"),
            color=alt.Color("Capa:N", scale=alt.Scale(range=["#374151", "#D6B46B", "#E8DCC0"])),
            order=alt.Order("Capa:N", sort="ascending"))
        st.altair_chart(ch.properties(height=260), use_container_width=True)


def _tornado(p):
    c = st.columns(2)
    var = c[0].slider("Variación de cada parámetro (±%)", 5, 50, 20, 5, key=k("t_var")) / 100
    met = c[1].radio("Medir el efecto sobre", ["SN requerido", "Espesor total"], horizontal=True, key=k("t_met"))
    filas = tornado(p, var, "sn" if met == "SN requerido" else "espesor")
    if not filas:
        st.info("Completá el diseño para ver la sensibilidad.")
        return
    if met == "SN requerido":
        base, lo_k, hi_k, tit = filas[0]["sn_base"], "sn_lo", "sn_hi", "SN requerido"
    else:
        base, lo_k, hi_k, tit = filas[0]["esp_base"], "esp_lo", "esp_hi", f"Espesor total ({filas[0]['unidad']})"
    datos = []
    for f in filas:
        datos.append({"Variable": f["etiqueta"], "Caso": f"−{var * 100:.0f} %", "desde": base, "hasta": f[lo_k],
                      "valor": auto(f["x_lo"])})
        datos.append({"Variable": f["etiqueta"], "Caso": f"+{var * 100:.0f} %", "desde": base, "hasta": f[hi_k],
                      "valor": auto(f["x_hi"])})
    orden = [f["etiqueta"] for f in filas]
    ch = alt.Chart(pd.DataFrame(datos)).mark_bar(height=18).encode(
        y=alt.Y("Variable:N", sort=orden, title=None),
        x=alt.X("desde:Q", title=tit, scale=alt.Scale(zero=False)), x2="hasta:Q",
        color=alt.Color("Caso:N", scale=alt.Scale(range=["#9CA3AF", "#C98A00"])),
        tooltip=["Variable", "Caso", "valor", alt.Tooltip("hasta:Q", title=tit, format=".3f")])
    regla = alt.Chart(pd.DataFrame({"b": [base]})).mark_rule(color="#1F2937").encode(x="b:Q")
    st.altair_chart((ch + regla).properties(height=45 * len(filas) + 40), use_container_width=True)
    top = filas[0]
    st.markdown(f"💡 La variable más influyente es **{top['etiqueta']}**: al variarla ±{var * 100:.0f} % el "
                f"{tit.lower()} va de {auto(top[lo_k])} a {auto(top[hi_k])}. "
                f"{VARIABLES[top['clave']].explicacion}")
    st.dataframe(pd.DataFrame([{"Variable": f["etiqueta"], "Valor actual": auto(f["x0"]),
                                f"Valor −{var * 100:.0f} %": auto(f["x_lo"]), f"Valor +{var * 100:.0f} %": auto(f["x_hi"]),
                                "SN −": f["sn_lo"], "SN +": f["sn_hi"], "Espesor −": f["esp_lo"], "Espesor +": f["esp_hi"]}
                               for f in filas]), hide_index=True, width="stretch",
                 column_config={x: st.column_config.NumberColumn(format="%.3f") for x in ("SN −", "SN +")})


def _escenarios(p, res):
    st.caption("El escenario «Proyecto actual» es tu diseño tal como está. Definí hasta tres alternativas "
               "cambiando los parámetros que quieras; los vacíos se mantienen iguales.")
    res_base = comparar_escenarios([("Proyecto actual", p)])[0]
    if res_base.get("sn_requerido") is None:
        st.info("Completá el diseño para comparar escenarios.")
        return
    escenarios = [("Proyecto actual", p)]
    cols = st.columns(3)
    sugerencias = [("Mayor confiabilidad", {"r_pct": 95.0}), ("Buen drenaje", {"m": 1.2}),
                   ("Subrasante mejorada", {"mr": round(res_base["mr"] * 1.5, -2)})]
    for i, col in enumerate(cols):
        nombre_def, cambios_def = sugerencias[i]
        with col:
            with st.container(border=True):
                nombre = st.text_input("Nombre", nombre_def, key=k(f"e_nom{i}"))
                q = p.copia()
                for clave, var in VARIABLES.items():
                    actual = var.leer(p, res)
                    v = st.number_input(f"{var.etiqueta} ({var.unidad})", value=float(cambios_def.get(clave, actual)),
                                        key=k(f"e_{i}_{clave}"), format="%.3f" if actual < 10 else "%.0f")
                    if abs(v - actual) > 1e-9:
                        var.escribir(q, v)
                escenarios.append((nombre, q))
    filas = comparar_escenarios(escenarios)
    tabla = pd.DataFrame([{
        "Escenario": f["escenario"], "W18": f.get("w18"), "M_R (psi)": f.get("mr"), "R (%)": f.get("r_pct"),
        "So": f.get("so"), "ΔPSI": f.get("dpsi"), "SN req.": f.get("sn_requerido"),
        "Carpeta": f.get("d1"), "Base": f.get("d2"), "Subbase": f.get("d3"), "Total": f.get("espesor_total"),
        "Cumple": "✔" if f.get("ok") else "✘"} for f in filas])
    seccion("Comparación")
    st.dataframe(tabla, hide_index=True, width="stretch", column_config={
        "W18": st.column_config.NumberColumn(format="%.0f"), "M_R (psi)": st.column_config.NumberColumn(format="%.0f"),
        "SN req.": st.column_config.NumberColumn(format="%.3f")})
    u = filas[0].get("unidad", "")
    datos = []
    for f in filas:
        if f.get("d1") is None:
            continue
        for capa, kk in (("1 · Carpeta", "d1"), ("2 · Base", "d2"), ("3 · Subbase", "d3")):
            datos.append({"Escenario": f["escenario"], "Capa": capa, "Espesor": f[kk]})
    ch = alt.Chart(pd.DataFrame(datos)).mark_bar().encode(
        x=alt.X("Escenario:N", sort=None, title=None),
        y=alt.Y("Espesor:Q", stack=True, title=f"Espesor ({u})", sort="descending"),
        color=alt.Color("Capa:N", scale=alt.Scale(range=["#374151", "#D6B46B", "#E8DCC0"])),
        order=alt.Order("Capa:N", sort="descending"),
        tooltip=["Escenario", "Capa", "Espesor"])
    st.altair_chart(ch.properties(height=320), use_container_width=True)
    base_tot = filas[0].get("espesor_total")
    for f in filas[1:]:
        if f.get("espesor_total") is not None and base_tot:
            dif = f["espesor_total"] - base_tot
            st.markdown(f"- **{f['escenario']}**: espesor total {num(f['espesor_total'], 1)} {u} "
                        f"({'+' if dif >= 0 else ''}{num(dif, 1)} {u} respecto del proyecto), "
                        f"SN requerido {num(f['sn_requerido'], 3)}.")


def render(res: dict):
    p = proyecto()
    encabezado("Sensibilidad y escenarios",
               "Cómo cambia el diseño cuando cambian los supuestos, y qué variable pesa más.", badge="±")
    concepto("¿Para qué sirve un análisis de sensibilidad?", CONCEPTO)
    if not res.get("capas"):
        st.info("Primero completá los módulos 1, 2 y 4 (o cargá un ejemplo desde Inicio).")
        return
    t1, t2, t3 = st.tabs(["📈 Curva de una variable", "🌪️ Tornado", "⚖️ Escenarios"])
    with t1:
        _curva(p)
    with t2:
        _tornado(p)
    with t3:
        _escenarios(p, res)
    st.caption(f"Proyecto actual: W18 = {entero(res['diseno']['w18'])} · M_R = {entero(res['diseno']['mr'])} psi · "
               f"SN requerido = {num(res['diseno']['sn_requerido'], 3)}")
