import pytest

from pavimentos.resiliente import DatosInvalidos, danio_relativo, mr_de_cbr, mr_efectivo


def test_mr_de_cbr_bajo():
    assert mr_de_cbr(4.7) == pytest.approx(7050, abs=0.5)


def test_mr_de_cbr_alto():
    assert mr_de_cbr(13.1) == pytest.approx(15972, abs=0.5)


def test_mr_de_cbr_fuera_de_rango():
    with pytest.raises(DatosInvalidos):
        mr_de_cbr(21.0)


def test_danio_relativo():
    assert danio_relativo(7050) == pytest.approx(0.1393, abs=1e-4)


PERIODOS = [
    {"nombre": "Ene-Mar", "meses": 3, "mr": 7050},
    {"nombre": "Abr", "meses": 1, "mr": 10050},
    {"nombre": "May/Nov/Dic", "meses": 3, "mr": 11965},
    {"nombre": "Jun-Oct", "meses": 5, "mr": 15972},
]


def test_mr_efectivo_practico3():
    r = mr_efectivo(PERIODOS)
    assert r["uf_bar"] == pytest.approx(0.0589, abs=1e-4)
    assert r["mr_efectivo"] == pytest.approx(10222, rel=0.005)


def test_meses_no_suman_12():
    with pytest.raises(DatosInvalidos):
        mr_efectivo(PERIODOS[:2])
