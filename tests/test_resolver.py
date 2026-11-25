import pytest

from pavimentos.modelo import Capa, Clima, Diseno, Periodo, ProyectoFlexible, Subrasante, Transito, Vehiculo
from pavimentos.resolver import minimos_aashto, resolver
from pavimentos.validacion import comparar, listar

EJERCICIOS = listar()


@pytest.mark.parametrize("ej", EJERCICIOS, ids=[e["id"] for e in EJERCICIOS])
def test_ejercicio_de_validacion(ej):
    r = comparar(ej)
    fallas = [f"{f['etiqueta']}: fuente {f['valor']} vs app {f['app']}" for f in r["filas"]
              if not f["cumple"] and f.get("tipo", "exacto") != "informativo"]
    assert r["aprobado"], fallas


def test_hay_cuatro_ejercicios():
    assert len(EJERCICIOS) >= 4


def test_examen_detecta_error_de_la_fuente_en_fila_4():
    ej = next(e for e in EJERCICIOS if e["id"].startswith("02"))
    fila4 = next(f for f in comparar(ej)["filas"] if f["clave"] == "transito.filas.3.w_bruto")
    assert not fila4["cumple"] and fila4["app"] == pytest.approx(1_895_619, rel=1e-4)


def _base() -> ProyectoFlexible:
    return ProyectoFlexible(
        transito=Transito(n=15, fd=0.5, fc=1.0, pt=2.0, sn_lef=3.0, vehiculos=[
            Vehiculo(nombre="Camión", tpda=100, r=0.03, pesado=True, ejes=[["simple", 7], ["tandem", 18]])]),
        subrasante=Subrasante(periodos=[Periodo("Seco", 8, cbr=6), Periodo("Húmedo", 4, cbr=4)]),
        diseno=Diseno(r_pct=90, so=0.45, p0=4.2, pt=2.0),
    )


def test_modulos_conectados():
    """El diseño usa el W18 del módulo 1 y el M_R del módulo 2 (no valores fijos)."""
    p = _base()
    r = resolver(p)
    assert r["ok"]
    assert r["diseno"]["w18"] == pytest.approx(r["transito"]["w18"])
    assert r["diseno"]["mr"] == pytest.approx(r["subrasante"]["mr_efectivo"])
    p.transito.vehiculos[0].tpda = 200
    r2 = resolver(p)
    assert r2["diseno"]["w18"] == pytest.approx(2 * r["diseno"]["w18"])
    assert r2["capas"]["sn3"] > r["capas"]["sn3"]


def test_clima_usa_el_transito_del_proyecto():
    p = _base()
    p.clima = Clima(activo=True, vr=2.0, ps=60, theta=0.1)
    a = resolver(p)["clima"]["periodo"]
    p.transito.vehiculos[0].tpda = 300
    b = resolver(p)["clima"]["periodo"]
    assert a != pytest.approx(b)


def test_roundtrip_json():
    p = _base()
    p.clima = Clima(activo=True, vr=1.0, ps=50)
    q = ProyectoFlexible.from_json(p.to_json())
    assert q == p
    assert resolver(q)["capas"]["sn_total"] == pytest.approx(resolver(p)["capas"]["sn_total"])


def test_error_si_meses_no_suman_12():
    p = _base()
    p.subrasante.periodos[0].meses = 5
    r = resolver(p)
    assert not r["ok"]
    assert any(a["nivel"] == "error" and a["modulo"] in ("subrasante", "diseno") for a in r["avisos"])


def test_error_si_falta_w18():
    p = ProyectoFlexible(diseno=Diseno(fuente_mr="dato", mr_dato=5000))
    r = resolver(p)
    assert not r["ok"] and any("W18" in a["texto"] for a in r["avisos"])


def test_dpsi_negativo_es_error():
    p = _base()
    p.diseno.p0, p.diseno.pt = 2.0, 2.5
    assert not resolver(p)["ok"]


def test_minimos_aashto():
    assert minimos_aashto(40_000) == (1.0, 4.0)
    assert minimos_aashto(1_000_000) == (3.0, 6.0)
    assert minimos_aashto(50_000_000) == (4.0, 6.0)


def test_minimo_gobierna_y_queda_registrado():
    p = _base()
    p.diseno.minimos = "personalizado"
    p.diseno.min_carpeta = 30.0
    r = resolver(p)
    assert r["capas"]["capas"][0]["d"] == 30.0
    assert any("mínimo" in d["texto"] for d in r["decisiones"])


def test_espesores_en_pulgadas():
    p = _base()
    p.diseno.unidad, p.diseno.paso_espesor = "pulg", 0.5
    r = resolver(p)
    for c in r["capas"]["capas"]:
        assert (c["d"] * 2) == pytest.approx(round(c["d"] * 2))
    assert r["capas"]["cumple"]


def _inicial():
    import json
    from pathlib import Path
    ruta = Path(__file__).resolve().parent.parent / "data" / "proyecto_inicial.json"
    return ProyectoFlexible.from_dict(json.loads(ruta.read_text(encoding="utf-8")))


def test_cargas_en_kip_equivalen_a_toneladas():
    from pavimentos.modelo import KIP_POR_T
    base = _inicial()
    en_kip = base.copia()
    en_kip.transito.unidad_carga = "kip"
    for v in en_kip.transito.vehiculos:
        v.ejes = [[t, c * KIP_POR_T] for t, c in v.ejes]
    a, b = resolver(base)["transito"]["w18"], resolver(en_kip)["transito"]["w18"]
    assert a == pytest.approx(b, rel=1e-9)


def test_aviso_si_el_sn_supuesto_esta_lejos():
    p = _inicial()
    r = resolver(p)                                  # supuesto 3, diseño 3,3: no hace falta repetir
    assert not any("Repetí" in a["texto"] for a in r["avisos"])
    p.transito.sn_lef = 6.0
    r = resolver(p)
    assert r["sn_sugerido"] == 3
    assert any("Repetí con la columna SN = 3" in a["texto"] for a in r["avisos"])


def test_fila_incompleta_se_marca():
    p = _inicial()
    p.transito.vehiculos[0].tpda = 0
    p.transito.vehiculos[1].ejes[1][1] = 0
    r = resolver(p)
    filas = r["transito"]["filas"]
    assert filas[0]["faltan"] == ["TPDA"]
    assert filas[1]["faltan"] == ["carga del eje 2"]
    assert filas[2]["faltan"] == []


def test_fc_fuera_de_rango_por_carriles():
    p = _inicial()
    p.transito.carriles, p.transito.fc = 3, 1.0
    assert any("Fc = 1" in a["texto"] for a in resolver(p)["avisos"])
    p.transito.fc = 0.7
    assert not any(a["texto"].startswith("Fc") for a in resolver(p)["avisos"])


def test_eje_sin_carga_es_error():
    p = ProyectoFlexible()
    p.transito.vehiculos = [Vehiculo(nombre="X", tpda=10, ejes=[["tandem", 0.0]])]
    res = resolver(p)
    assert any("falta la carga" in a["texto"] for a in res["avisos"])
