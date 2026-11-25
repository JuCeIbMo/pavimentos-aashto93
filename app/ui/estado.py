"""Estado compartido de la app: un único ProyectoFlexible en session_state.

Todas las páginas leen y escriben `proyecto()`; `resultado()` lo resuelve completo
en cada recarga (es rápido), así los módulos están siempre conectados.

`ver()` es un contador que cambia al cargar/crear un proyecto: va en las `key` de
los widgets para que se reinicien con los valores del proyecto nuevo.
"""

from __future__ import annotations

import streamlit as st

from pavimentos.modelo import ProyectoFlexible
from pavimentos.resolver import resolver


def proyecto() -> ProyectoFlexible:
    if "proyecto" not in st.session_state or not isinstance(st.session_state["proyecto"], ProyectoFlexible):
        st.session_state["proyecto"] = proyecto_inicial()
        st.session_state["ver"] = st.session_state.get("ver", 0) + 1
    return st.session_state["proyecto"]


def ver() -> int:
    return st.session_state.setdefault("ver", 0)


def k(nombre: str) -> str:
    """Key de widget ligada a la versión del proyecto cargado."""
    return f"{nombre}__{ver()}"


def reemplazar(p: ProyectoFlexible):
    st.session_state["proyecto"] = p
    st.session_state["ver"] = ver() + 1
    st.session_state.pop("pdf_bytes", None)
    st.session_state.pop("xlsx_bytes", None)


def resultado() -> dict:
    return resolver(proyecto())


def proyecto_inicial() -> ProyectoFlexible:
    """Proyecto de arranque: el práctico 3, para que todo se vea funcionando."""
    from pavimentos.validacion import listar

    for e in listar():
        if e["id"].startswith("01"):
            p = ProyectoFlexible.from_dict(e["proyecto"])
            p.nombre = "Mi proyecto (basado en el Práctico 3)"
            return p
    return ProyectoFlexible()


def refrescar():
    """Reinicia los widgets para que relean el proyecto (tras agregar/borrar filas)."""
    st.session_state["ver"] = ver() + 1
    st.session_state.pop("pdf_bytes", None)
    st.session_state.pop("xlsx_bytes", None)
