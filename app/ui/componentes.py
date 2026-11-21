"""Componentes reutilizables de la interfaz Streamlit."""

import json
import os

import streamlit as st


# --------------------------------------------------------------------------- #
#  Bloques visuales (dependen del CSS de theme.py)                            #
# --------------------------------------------------------------------------- #
def encabezado(titulo: str, descripcion: str = "", badge: str = ""):
    st.markdown(
        f"""<div class="page-head">
              <div class="page-badge">{badge}</div>
              <div><h1 class="page-title">{titulo}</h1>
              <p class="page-sub">{descripcion}</p></div>
            </div>""",
        unsafe_allow_html=True,
    )


def seccion(titulo: str, descripcion: str = ""):
    st.markdown(
        f"""<div class="section-title">{titulo}</div>
            <div class="section-sub">{descripcion}</div>""",
        unsafe_allow_html=True,
    )


def tarjeta(etiqueta: str, valor: str, sub: str = ""):
    st.markdown(
        f"""<div class="kpi-card">
              <div class="kpi-label">{etiqueta}</div>
              <div class="kpi-value">{valor}</div>
              {f'<div class="kpi-sub">{sub}</div>' if sub else ''}
            </div>""",
        unsafe_allow_html=True,
    )


def fila_metricas(items: list, ncols: int | None = None):
    """Items: lista de dicts {etiqueta, valor, sub} o tuplas (etiqueta, valor[, sub])."""
    n = ncols or len(items)
    cols = st.columns(n)
    for i, it in enumerate(items):
        if isinstance(it, dict):
            et, va, su = it["etiqueta"], it["valor"], it.get("sub", "")
        else:
            et, va = it[0], it[1]
            su = it[2] if len(it) > 2 else ""
        with cols[i % n]:
            tarjeta(et, va, su)


# --------------------------------------------------------------------------- #
#  Componentes funcionales                                                    #
# --------------------------------------------------------------------------- #
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


def a_csv(datos: list[dict]) -> str:
    """Convierte una lista de dicts a CSV (coma decimal, separador ';')."""
    if not datos:
        return ""
    claves = list(datos[0].keys())
    lineas = [";".join(claves)]
    for d in datos:
        fila = []
        for k in claves:
            v = d.get(k)
            if isinstance(v, float):
                fila.append(f"{v:.4f}".replace(".", ","))
            else:
                fila.append(str(v))
        lineas.append(";".join(fila))
    return "\n".join(lineas)
