"""Prueba de humo de la interfaz: cada página se renderiza sin excepciones."""

import os

import pytest
from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(__file__), "..", "app", "app.py")
PAGINAS = ["Inicio", "1 · Tránsito", "2 · Subrasante", "4 · Diseño flexible", "6 · Clima",
           "Sensibilidad y escenarios", "Validación", "Referencias"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_sin_errores(pagina):
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["pagina_actual"] = pagina
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_cargar_ejemplos_desde_inicio():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    for b in at.button:
        if b.key and b.key.startswith("ej_02"):
            b.click()
            break
    at.run()
    assert not at.exception
    assert "Examen" in at.session_state["proyecto"].nombre
