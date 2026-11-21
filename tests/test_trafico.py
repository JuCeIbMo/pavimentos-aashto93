import json

import pytest

from pavimentos.lef import cargar_lef
from pavimentos.trafico import esal_total, esal_vehiculo, factor_camion, factor_crecimiento, w_t

T = cargar_lef()
with open("data/validacion/practico3.json") as f:
    P = json.load(f)


def test_factor_crecimiento():
    assert factor_crecimiento(0.02, 15) == pytest.approx(17.293, abs=1e-2)
    assert factor_crecimiento(0.03, 20) == pytest.approx(26.87, abs=1e-2)
    assert factor_crecimiento(0.0, 15) == 15.0


CAMION = {"nombre": "Camión mediano", "tpda": 32, "r": 0.02, "pesado": True,
          "ejes": [["simple", 7], ["simple", 11]]}


def test_camion_mediano():
    r = esal_vehiculo(CAMION, 15, 0.5, 1.0, T, 2.0, 3)
    assert r["fc"] == pytest.approx(2.704, abs=1e-3)
    assert r["esal1"] == pytest.approx(15791, abs=1.0)
    assert r["w"] == pytest.approx(273087, rel=0.005)


def test_total_practico3():
    r = esal_total(P["vehiculos"], 15, 0.5, 1.0, T, 2.0, 3)
    assert r["total_w"] == pytest.approx(890521, rel=0.005)


def test_w_t_continuo():
    assert w_t(P["vehiculos"], 15, 0.5, 1.0, T, 2.0, 3) == pytest.approx(890521, rel=0.005)


def test_factor_camion_camion():
    assert factor_camion(CAMION, T, 2.0, 3) == pytest.approx(2.704, abs=1e-3)
