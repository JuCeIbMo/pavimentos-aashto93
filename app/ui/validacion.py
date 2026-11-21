"""Página de validación: reproduce el práctico 3 y compara con los valores esperados."""

import math

import streamlit as st

from pavimentos.ambiental import periodo_desempeno
from pavimentos.flexible import disenar_capas, r_etapa, sn_requerido, zr_de_r
from pavimentos.lef import cargar_lef
from pavimentos.resiliente import mr_efectivo
from pavimentos.trafico import esal_total, w_t

from .componentes import cargar_practico3, encabezado, tabla

ESPERADOS = {
    "M_R efectivo (psi)": 10222.0,
    "W15 (ESAL)": 890521.0,
    "SN (adoptado)": 3.1,
    "Período desempeño (años)": 14.8,
    "Espesores (cm)": "13 / 15 / 10",
}


def render():
    encabezado("Validación · Práctico 3",
               "Reproduce el Práctico 3 y compara contra los valores de referencia.",
               badge="✓")

    if not st.button("Ejecutar validación del práctico 3", type="primary"):
        st.info("Corré la validación para comparar el paquete contra el práctico 3.")
        return

    tablas = cargar_lef()
    preset = cargar_practico3()
    periodos = [
        {"nombre": "Ene-Mar", "meses": 3, "mr": 7050},
        {"nombre": "Abr", "meses": 1, "mr": 10050},
        {"nombre": "May/Nov/Dic", "meses": 3, "mr": 11965},
        {"nombre": "Jun-Oct", "meses": 5, "mr": 15972},
    ]

    mr = mr_efectivo(periodos)["mr_efectivo"]
    w15 = esal_total(preset["vehiculos"], 15, 0.5, 1.0, tablas, 2.0, 3)["total_w"]
    zr = zr_de_r(r_etapa(85.0, 2))
    sn_exacto = sn_requerido(w15, zr, 0.49, 2.2, mr)
    sn = math.ceil(sn_exacto * 10) / 10
    w_t_fn = lambda t: w_t(preset["vehiculos"], t, 0.5, 1.0, tablas, 2.0, 3)
    amb = periodo_desempeno(sn, mr, 2.2, zr, 0.49, 2.0, 60.0, 0.1, 15, w_t_fn)
    cap = disenar_capas(amb["w_adm"], zr, 0.49, amb["dpsi_tr"], mr,
                        28143, 16199, 0.428, 0.131, 0.117, 1.0, 1.0, 7.5, 15.0, 10.0)

    obtenidos = {
        "M_R efectivo (psi)": round(mr, 0),
        "W15 (ESAL)": round(w15, 0),
        "SN (adoptado)": sn,
        "Período desempeño (años)": round(amb["periodo"], 2),
        "Espesores (cm)": f"{cap['d1_cm']:.0f} / {cap['d2_cm']:.0f} / {cap['d3_cm']:.0f}",
    }

    filas = []
    for clave, esperado in ESPERADOS.items():
        ok = False
        if clave == "SN (adoptado)":
            ok = abs(obtenidos[clave] - esperado) < 0.02
        elif clave == "Período desempeño (años)":
            ok = abs(obtenidos[clave] - esperado) < 0.1
        elif clave == "M_R efectivo (psi)":
            ok = abs(obtenidos[clave] - esperado) / esperado < 0.005
        elif clave == "W15 (ESAL)":
            ok = abs(obtenidos[clave] - esperado) / esperado < 0.005
        else:
            ok = str(obtenidos[clave]) == str(esperado)
        filas.append({"Resultado": clave, "Esperado": str(esperado), "Obtenido": str(obtenidos[clave]),
                      "Estado": "✅" if ok else "❌"})

    tabla(filas, ["Resultado", "Esperado", "Obtenido", "Estado"])
    if all(f["Estado"] == "✅" for f in filas):
        st.success("El paquete reproduce el práctico 3 dentro de tolerancia.")
    else:
        st.error("Hay discrepancias con el práctico 3.")
