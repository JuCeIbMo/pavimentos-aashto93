import pytest

from pavimentos.flexible import (
    coef_a1, coef_a2, coef_a3, disenar_capas, log_w18, r_etapa, sn_requerido, zr_de_r,
)


def test_zr():
    assert zr_de_r(90.0) == pytest.approx(-1.282, abs=1e-3)
    assert zr_de_r(85.0) == pytest.approx(-1.036, abs=1e-3)


def test_r_etapa():
    assert r_etapa(85.0, 2) == pytest.approx(92.195, abs=1e-2)


def test_coeficientes():
    assert coef_a1(400000) == pytest.approx(0.4175, abs=1e-4)
    assert coef_a2(30000) == pytest.approx(0.1378, abs=1e-4)
    assert coef_a3(11000) == pytest.approx(0.0784, abs=1e-4)


def test_sn_practico3():
    # la raíz exacta de la ecuación es ~3.05; el práctico ADOPTA 3.1 redondeando arriba
    sn = sn_requerido(w18=890521, zr=-1.419, so=0.49, delta_psi=2.2, mr=10222)
    assert sn == pytest.approx(3.05, abs=0.02)


def test_capas_practico3():
    r = disenar_capas(
        w18=859000, zr=-1.419, so=0.49, delta_psi=1.888, mr=10222,
        e_b=28143, e_sb=16199, a1=0.428, a2=0.131, a3=0.117,
        m2=1.0, m3=1.0, min_ca_cm=7.5, min_base_cm=15.0, min_subbase_cm=10.0)
    assert r["sn3"] == pytest.approx(3.10, abs=0.02)
    assert r["d1_cm"] == 13.0
    assert r["d2_cm"] == 15.0
    assert r["d3_cm"] == 10.0
    assert r["cumple"] is True
