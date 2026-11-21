"""Componentes reutilizables de la interfaz Streamlit."""

import json
import os

import streamlit as st


def tarjeta(titulo: str, valor: str, ayuda: str | None = None):
    st.metric(titulo, valor, help=ayuda)


def tabla(datos: list[dict], columnas: list[str] | None = None):
    if columnas:
        datos = [{c: d.get(c) for c in columnas} for d in datos]
    st.dataframe(datos, width="stretch", hide_index=True)


def aviso(mensaje: str, tipo: str = "info"):
    if tipo == "error":
        st.error(mensaje)
    elif tipo == "warn":
        st.warning(mensaje)
    else:
        st.info(mensaje)


def cargar_practico3() -> dict:
    """Carga el preset del práctico 3 (composición vehicular)."""
    ruta = os.path.join(os.path.dirname(__file__), "..", "..", "data", "validacion", "practico3.json")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def ejes_a_str(ejes: list) -> str:
    return "; ".join(f"{tipo} {carga}" for tipo, carga in ejes)


def str_a_ejes(s: str) -> list:
    ejes = []
    for parte in s.replace(",", ";").split(";"):
        parte = parte.strip()
        if not parte:
            continue
        tipo, carga = parte.split()
        ejes.append([tipo, float(carga)])
    return ejes
