import json
import math

import pytest

from pavimentos.ambiental import periodo_desempeno
from pavimentos.flexible import disenar_capas, r_etapa, sn_requerido, zr_de_r
from pavimentos.lef import cargar_lef
from pavimentos.resiliente import mr_efectivo
from pavimentos.trafico import esal_total, w_t

T = cargar_lef()
with open("data/validacion/practico3.json") as f:
    P = json.load(f)

PERIODOS = [
    {"nombre": "Ene-Mar", "meses": 3, "mr": 7050},
    {"nombre": "Abr", "meses": 1, "mr": 10050},
    {"nombre": "May/Nov/Dic", "meses": 3, "mr": 11965},
    {"nombre": "Jun-Oct", "meses": 5, "mr": 15972},
]


def test_practico3_completo():
    # 1) M_R efectivo
    mr = mr_efectivo(PERIODOS)["mr_efectivo"]
    # 2) tránsito
    w15 = esal_total(P["vehiculos"], 15, 0.5, 1.0, T, 2.0, 3)["total_w"]
    # 3) confiabilidad por etapas
    zr = zr_de_r(r_etapa(85.0, 2))
    # 4) SN exacto y adopción (redondeo a 0.1)
    sn_exacto = sn_requerido(w15, zr, 0.49, 2.2, mr)
    sn = math.ceil(sn_exacto * 10) / 10
    # 5) período de desempeño con hinchamiento
    w_t_fn = lambda t: w_t(P["vehiculos"], t, 0.5, 1.0, T, 2.0, 3)
    amb = periodo_desempeno(sn, mr, 2.2, zr, 0.49, 2.0, 60.0, 0.1, 15, w_t_fn)
    # 6) espesores con el tráfico y ΔPSI remanente ajustados
    cap = disenar_capas(amb["w_adm"], zr, 0.49, amb["dpsi_tr"], mr,
                        28143, 16199, 0.428, 0.131, 0.117, 1.0, 1.0, 7.5, 15.0, 10.0)

    assert mr == pytest.approx(10222, rel=0.005)
    assert w15 == pytest.approx(890521, rel=0.005)
    assert sn == 3.1
    assert amb["periodo"] == pytest.approx(14.8, abs=0.1)
    assert amb["w_adm"] == pytest.approx(859000, rel=0.01)
    assert (cap["d1_cm"], cap["d2_cm"], cap["d3_cm"]) == (13.0, 15.0, 10.0)
