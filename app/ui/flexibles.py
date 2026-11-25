"""Módulo 4 — Diseño estructural de pavimentos flexibles."""

import pandas as pd
import streamlit as st

from pavimentos.formato import entero, num, pct
from pavimentos.modelo import Capa
from pavimentos.unidades import KG_CM2_A_PSI

from .componentes import (avisos, concepto, decisiones, ecuacion, encabezado, estructura, fila_metricas,
                          seccion)
from .estado import k, proyecto

CONCEPTO = """
La ecuación AASHTO 93 relaciona **cuántas repeticiones de carga (W<sub>18</sub>)** soporta un pavimento
con su **número estructural SN** antes de perder la serviciabilidad ΔPSI, para una subrasante de
módulo M<sub>R</sub> y con una confiabilidad R.

- **SN** es un índice abstracto de "capacidad estructural". Después se traduce en espesores:
  SN = a<sub>1</sub>D<sub>1</sub> + a<sub>2</sub>m<sub>2</sub>D<sub>2</sub> + a<sub>3</sub>m<sub>3</sub>D<sub>3</sub>.
- **a<sub>i</sub>** (coeficiente de capa): cuánto SN aporta cada pulgada de material. Un concreto asfáltico
  aporta unas tres veces más que una base granular.
- **m<sub>i</sub>** (drenaje): si el agua sale rápido y la capa rara vez se satura, m > 1 y la capa rinde más.
- **Confiabilidad:** Z<sub>R</sub>·S<sub>o</sub> "infla" el tránsito para cubrir la incertidumbre. Con R = 50 %, Z<sub>R</sub> = 0.

**Diseño por capas:** cada capa protege a la que está debajo. La carpeta se dimensiona como si la base
fuera la subrasante (SN<sub>1</sub> con E<sub>B</sub>); carpeta + base, como si la subbase fuera la subrasante
(SN<sub>2</sub> con E<sub>SB</sub>); y el conjunto, para la subrasante real (SN<sub>3</sub> con M<sub>R</sub>).
"""

AYUDA_R = """Confiabilidad recomendada (AASHTO 93, tabla 2.2), urbano / rural:
Autopistas interestatales 85–99,9 / 80–99,9 · Arterias principales 80–99 / 75–95 ·
Colectoras 80–95 / 75–95 · Locales 50–80 / 50–80."""
AYUDA_SO = "Desviación estándar global. Flexibles: 0,40–0,50 (0,45 típico; 0,49 si el tránsito es poco preciso)."
AYUDA_P0 = "Serviciabilidad inicial. AASHO Road Test: 4,2 para flexibles."
AYUDA_PT = "Serviciabilidad terminal: 2,5 o más para vías principales; 2,0 para tránsito menor."
AYUDA_ETAPAS = "Si se construye por etapas (p. ej. pavimento inicial + recapado), cada etapa usa R^(1/n)."

# AASHTO 93, tabla 2.4: valores de m por calidad de drenaje y % del tiempo cerca de la saturación
TABLA_M = {
    "Excelente (½ día)": [(1.40, 1.35), (1.35, 1.30), (1.30, 1.20), (1.20, 1.20)],
    "Bueno (1 día)": [(1.35, 1.25), (1.25, 1.15), (1.15, 1.00), (1.00, 1.00)],
    "Regular (1 semana)": [(1.25, 1.15), (1.15, 1.05), (1.00, 0.80), (0.80, 0.80)],
    "Pobre (1 mes)": [(1.15, 1.05), (1.05, 0.80), (0.80, 0.60), (0.60, 0.60)],
    "Muy pobre (no drena)": [(1.05, 0.95), (0.95, 0.75), (0.75, 0.40), (0.40, 0.40)],
}
EXPOSICION = ["< 1 %", "1 – 5 %", "5 – 25 %", "> 25 %"]


def _capa_granular(titulo: str, capa: Capa, clave: str, cbr_def: float):
    st.markdown(f"**{titulo}**")
    modos = ["CBR del material", "Módulo E (psi)"]
    modo = st.radio("Dato disponible", modos, index=0 if capa.e_psi is None else 1, horizontal=True,
                    key=k(f"{clave}_modo"), label_visibility="collapsed")
    if modo == modos[0]:
        capa.cbr = st.number_input("CBR (%)", 1.0, 100.0, float(capa.cbr or cbr_def), 1.0, key=k(f"{clave}_cbr"),
                                   help="El módulo se estima con la correlación de Cabezas (2006).")
        capa.e_psi = None
    else:
        capa.e_psi = st.number_input("E (psi)", 1000.0, 200000.0, float(capa.e_psi or 20000.0), 500.0,
                                     key=k(f"{clave}_e"))
        capa.cbr = None
    usar_a = st.checkbox("Ingresar a directamente", value=capa.a is not None, key=k(f"{clave}_adato"),
                         help="Por ejemplo, si lo leíste de las figuras 2.6 / 2.7 de la guía.")
    capa.a = st.number_input("a", 0.01, 0.30, float(capa.a or 0.12), 0.005, format="%.4f",
                             key=k(f"{clave}_a")) if usar_a else None
    capa.m = st.number_input("Coeficiente de drenaje m", 0.40, 1.40, float(capa.m), 0.05, key=k(f"{clave}_m"),
                             help="Ver el asistente de drenaje más abajo (tabla 2.4 de AASHTO).")


def render(res: dict):
    p = proyecto()
    d = p.diseno
    encabezado("Diseño de pavimentos flexibles",
               "Número estructural requerido y espesores de carpeta, base y subbase.", badge="04")
    concepto("¿Cómo funciona la ecuación AASHTO 93?", CONCEPTO)

    # ---------------- Parámetros
    seccion("Tránsito y subrasante", "Por defecto se toman de los módulos 1 y 2; también se pueden ingresar como dato.")
    c = st.columns(2)
    tr, sub = res.get("transito"), res.get("subrasante")
    with c[0]:
        op = ["Del módulo 1 (tránsito)", "Dato conocido"]
        sel = st.radio("W18 de diseño", op, index=0 if d.fuente_w18 == "calculado" else 1, horizontal=True,
                       key=k("d_fw"))
        d.fuente_w18 = "calculado" if sel == op[0] else "dato"
        if d.fuente_w18 == "dato":
            d.w18_dato = st.number_input("W18 (ESAL)", 1.0, 1e9, float(d.w18_dato or (tr or {}).get("w18") or 1e6),
                                         10000.0, format="%.0f", key=k("d_w"))
        else:
            st.markdown(f"W18 = **{entero(tr['w18'])}** ESAL" if tr else "⚠️ Falta calcular el módulo 1.")
    with c[1]:
        op = ["Del módulo 2 (subrasante)", "Dato conocido"]
        sel = st.radio("M_R efectivo", op, index=0 if d.fuente_mr == "calculado" else 1, horizontal=True,
                       key=k("d_fmr"))
        d.fuente_mr = "calculado" if sel == op[0] else "dato"
        if d.fuente_mr == "dato":
            d.mr_dato = st.number_input("M_R (psi)", 500.0, 50000.0,
                                        float(d.mr_dato or (sub or {}).get("mr_efectivo") or 7000), 100.0,
                                        key=k("d_mr"))
        else:
            st.markdown(f"M_R = **{entero(sub['mr_efectivo'])}** psi" if sub else "⚠️ Falta calcular el módulo 2.")

    seccion("Confiabilidad y serviciabilidad")
    c = st.columns(5)
    d.r_pct = c[0].number_input("Confiabilidad R (%)", 50.0, 99.99, float(d.r_pct), 1.0, key=k("d_r"), help=AYUDA_R)
    d.etapas = int(c[1].number_input("Etapas", 1, 4, int(d.etapas), 1, key=k("d_et"), help=AYUDA_ETAPAS))
    d.so = c[2].number_input("Desviación So", 0.30, 0.60, float(d.so), 0.01, key=k("d_so"), help=AYUDA_SO)
    d.p0 = c[3].number_input("p0 inicial", 3.0, 5.0, float(d.p0), 0.1, key=k("d_p0"), help=AYUDA_P0)
    d.pt = c[4].number_input("pt terminal", 1.5, 3.5, float(d.pt), 0.1, key=k("d_pt"), help=AYUDA_PT)

    # ---------------- Materiales
    seccion("Materiales", "Coeficientes estructurales a partir del módulo de cada material.")
    c = st.columns(3)
    with c[0]:
        st.markdown("**Carpeta asfáltica**")
        unidad_e = st.radio("Unidad", ["kg/cm²", "psi"], horizontal=True, key=k("ca_u"), label_visibility="collapsed")
        e_actual = d.carpeta.e_psi or 400000.0
        if unidad_e == "kg/cm²":
            mostrado = round(e_actual / KG_CM2_A_PSI, 0)
            e = st.number_input("E concreto asfáltico (kg/cm²)", 5000.0, 60000.0, mostrado,
                                100.0, key=k("ca_e_kg"), help="Módulo elástico a 20 °C. 29.880 kg/cm² ≈ 425.000 psi.")
            if e != mostrado:  # solo si el usuario lo cambió: no alterar el valor cargado por redondeo
                d.carpeta.e_psi = e * KG_CM2_A_PSI
        else:
            d.carpeta.e_psi = st.number_input("E concreto asfáltico (psi)", 70000.0, 800000.0, float(e_actual),
                                              5000.0, key=k("ca_e_psi"))
        usar_a = st.checkbox("Ingresar a₁ directamente", value=d.carpeta.a is not None, key=k("ca_adato"))
        d.carpeta.a = st.number_input("a₁", 0.10, 0.60, float(d.carpeta.a or 0.42), 0.005, format="%.4f",
                                      key=k("ca_a")) if usar_a else None
    with c[1]:
        _capa_granular("Base granular", d.base, "b", 80.0)
    with c[2]:
        _capa_granular("Subbase granular", d.subbase, "sb", 30.0)

    with st.expander("🧭 Asistente de drenaje (AASHTO 93, tabla 2.4)"):
        a1, a2 = st.columns(2)
        calidad = a1.selectbox("Calidad del drenaje (tiempo en que se elimina el agua)", list(TABLA_M), index=1,
                               key=k("dr_cal"))
        expo = a2.selectbox("% del tiempo en que la capa está cerca de la saturación", EXPOSICION, index=2,
                            key=k("dr_exp"))
        hi, lo = TABLA_M[calidad][EXPOSICION.index(expo)]
        st.markdown(f"Rango AASHTO: **m = {num(lo, 2)} – {num(hi, 2)}** → valor medio {num((hi + lo) / 2, 2)}")
        st.dataframe(pd.DataFrame({e: [f"{num(r[i][1], 2)} – {num(r[i][0], 2)}" for r in TABLA_M.values()]
                                   for i, e in enumerate(EXPOSICION)}, index=list(TABLA_M)), width="stretch")

    # ---------------- Criterios
    seccion("Criterios de redondeo y espesores mínimos")
    c = st.columns(4)
    unidad = c[0].selectbox("Unidad de espesores", ["cm", "pulg"], index=0 if d.unidad == "cm" else 1, key=k("d_un"))
    if unidad != d.unidad:
        d.unidad = unidad
    d.paso_espesor = c[1].number_input(f"Redondear espesores a ({d.unidad})", 0.1, 5.0, float(d.paso_espesor), 0.5,
                                       key=k("d_paso"), help="Se redondea siempre hacia arriba.")
    d.paso_sn = c[2].number_input("Redondear SN a", 0.0, 1.0, float(d.paso_sn), 0.05, key=k("d_psn"),
                                  help="0 = no redondear. La cátedra y la guía adoptan el SN redondeado a 0,1.")
    modos = {"aashto": "Tabla AASHTO (según W18)", "personalizado": "Personalizados", "ninguno": "Sin mínimos"}
    sel = c[3].selectbox("Espesores mínimos", list(modos.values()), index=list(modos).index(d.minimos), key=k("d_min"))
    d.minimos = [x for x, v in modos.items() if v == sel][0]
    if d.minimos == "personalizado":
        c = st.columns(3)
        d.min_carpeta = c[0].number_input(f"Mínimo carpeta ({d.unidad})", 0.0, 50.0, float(d.min_carpeta), 0.5, key=k("mn1"))
        d.min_base = c[1].number_input(f"Mínimo base ({d.unidad})", 0.0, 80.0, float(d.min_base), 0.5, key=k("mn2"))
        d.min_subbase = c[2].number_input(f"Mínimo subbase ({d.unidad})", 0.0, 80.0, float(d.min_subbase), 0.5, key=k("mn3"))
    elif d.minimos == "aashto":
        st.caption("Tabla AASHTO 93 (Parte II, 3.1.5): W18 ≤ 50.000 → 1\" / 4\" · ≤ 150.000 → 2\" / 4\" · "
                   "≤ 500.000 → 2,5\" / 4\" · ≤ 2.000.000 → 3\" / 6\" · ≤ 7.000.000 → 3,5\" / 6\" · más → 4\" / 6\" "
                   "(carpeta / base).")

    # ---------------- Resultados
    avisos(res, "diseno")
    di, ca = res.get("diseno"), res.get("capas")
    if not (di and ca):
        return
    seccion("Resultados")
    fila_metricas([
        {"etiqueta": "SN requerido", "valor": num(di["sn_requerido"], 3), "sub": f"adoptado {num(di['sn_adoptado'], 2)}"},
        {"etiqueta": "Z_R", "valor": num(di["zr"], 3), "sub": f"R por etapa = {pct(di['r_etapa'], 2)}"},
        {"etiqueta": "SN aportado", "valor": num(ca["sn_total"], 3), "sub": "✔ cumple" if ca["cumple"] else "✘ no cumple"},
        {"etiqueta": "Espesor total", "valor": f"{num(ca['espesor_total'], 1)} {ca['unidad']}",
         "sub": f"W usado: {entero(ca['w_diseno'])}"},
    ])
    c1, c2 = st.columns([0.85, 1.4])
    with c1:
        estructura(ca, di["mr"])
    with c2:
        u = ca["unidad"]
        otra = "cm" if u == "pulg" else "pulg"
        st.dataframe(pd.DataFrame([{
            "Capa": x["capa"].replace(" granular", "").replace("Carpeta asfáltica", "Carpeta"), "a": x["a"],
            "m": x["m"], "SN req.": x["sn_req"], f"D calc. ({u})": x["d_calc"],
            f"D adopt. ({u})": x["d"], f"D ({otra})": x["d_cm"] if u == "pulg" else x["d_pulg"],
            "SN aporte": x["sn_aporte"]} for x in ca["capas"]]), hide_index=True, width="stretch",
            column_config={**{c: st.column_config.NumberColumn(format="%.3f") for c in ("a", "SN req.", "SN aporte")},
                           "m": st.column_config.NumberColumn(format="%.2f"),
                           **{c: st.column_config.NumberColumn(format="%.2f")
                              for c in (f"D calc. ({u})", f"D adopt. ({u})", f"D ({otra})")}})
        for v in ca["verificaciones"]:
            icono = "✅" if v["cumple"] else "❌"
            st.markdown(f"{icono} {v['criterio']}: {num(v['izq'], 3)} ≥ {num(v['der'], 3)}")
    mat = di["materiales"]
    st.caption(f"E base = {entero(mat['base']['e'])} psi ({mat['base']['origen_e']}) · "
               f"E subbase = {entero(mat['subbase']['e'])} psi ({mat['subbase']['origen_e']}) · "
               f"a₁ = {num(mat['carpeta']['a'], 4)} · a₂ = {num(mat['base']['a'], 4)} · a₃ = {num(mat['subbase']['a'], 4)}")
    decisiones(res, "diseno")

    with st.expander("📐 Procedimiento y ecuaciones"):
        ecuacion("zr")
        ecuacion("aashto")
        st.markdown(f"Con log W18 = {num(di['log_w18'], 3)}, Z_R = {num(di['zr'], 3)}, So = {num(di['so'], 2)}, "
                    f"ΔPSI = {num(di['dpsi'], 2)} y M_R = {entero(di['mr'])} psi → **SN = {num(di['sn_requerido'], 3)}**. "
                    f"Comprobación: con ese SN la ecuación da log W = {num(di['log_w_admisible'], 3)} "
                    f"(SN adoptado).")
        ecuacion("e_cbr")
        ecuacion("coef")
        ecuacion("sn")
        ecuacion("capas")
