import math

import pytest

from pavimentos.ambiental import (
    DatosInvalidos, delta_psi_helada, delta_psi_hinchamiento, periodo_desempeno,
)


def test_hinchamiento():
    assert delta_psi_hinchamiento(2.0, 60.0, 0.1, 15) == pytest.approx(0.312, abs=1e-3)


def test_helada_formula():
    assert delta_psi_helada(50.0, 1.0, 20.0, 10) == pytest.approx(
        0.01 * 50 * 1 * (1 - math.exp(-0.02 * 20 * 10)), abs=1e-9)


def test_periodo_simple():
    # w_t creciente normalizado; ambiente que deja margen de serviciabilidad
    w_t_fn = lambda t: 890521 * (1.02 ** t - 1) / (1.02 ** 15 - 1)
    r = periodo_desempeno(sn=3.1, mr=10222, delta_psi_total=2.2, zr=-1.419, so=0.49,
                           vr=2.0, ps=60.0, theta=0.1, t_inicial=15, w_t_fn=w_t_fn)
    assert 0 < r["dpsi_tr"] < 2.2
    assert r["periodo"] > 0


def test_ambiente_consume_todo():
    with pytest.raises(DatosInvalidos):
        periodo_desempeno(sn=3.1, mr=10222, delta_psi_total=0.2, zr=-1.419, so=0.49,
                          vr=2.0, ps=60.0, theta=0.1, t_inicial=15, w_t_fn=lambda t: 1000)
