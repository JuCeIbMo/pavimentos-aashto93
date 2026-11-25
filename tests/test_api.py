"""La API expone el motor sin alterar resultados."""

import pytest
from fastapi.testclient import TestClient

from api.main import app

c = TestClient(app)


@pytest.fixture(scope="module")
def inicial():
    return c.get("/api/proyecto/inicial").json()


def test_resolver_practico3():
    ej = next(e for e in c.get("/api/ejemplos").json() if e["id"].startswith("01"))
    r = c.post("/api/resolver", json={"proyecto": ej["proyecto"]}).json()
    assert r["ok"]
    assert r["transito"]["w18"] == pytest.approx(890521, rel=1e-3)
    assert [x["d"] for x in r["capas"]["capas"]] == [13, 15, 10]


def test_ejemplos_y_validacion():
    ej = c.get("/api/ejemplos").json()
    assert len(ej) >= 4
    val = c.get("/api/validacion").json()
    assert all(v["aprobado"] for v in val)


def test_exportar(inicial):
    pdf = c.post("/api/exportar/pdf", json={"proyecto": inicial})
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    xl = c.post("/api/exportar/excel", json={"proyecto": inicial})
    assert xl.status_code == 200 and xl.content[:2] == b"PK"


def test_exportar_incompleto_da_400():
    vacio = c.get("/api/proyecto/nuevo").json()
    assert c.post("/api/exportar/pdf", json={"proyecto": vacio}).status_code == 400


def test_sensibilidad(inicial):
    b = c.post("/api/sensibilidad/barrido", json={"proyecto": inicial, "variable": "mr", "n": 7}).json()
    assert len(b["puntos"]) == 7
    t = c.post("/api/sensibilidad/tornado", json={"proyecto": inicial}).json()
    assert t and t[0]["rango_sn"] >= t[-1]["rango_sn"]
    e = c.post("/api/sensibilidad/escenarios",
               json={"proyecto": inicial, "escenarios": [{"nombre": "R 95", "cambios": {"r_pct": 95}}]}).json()
    assert e[1]["sn_requerido"] > e[0]["sn_requerido"]


def test_catalogo_y_referencias():
    cat = c.get("/api/catalogo").json()
    assert cat["opciones"] and all(c == 0 for o in cat["opciones"] for _, c in o["ejes"])
    ref = c.get("/api/referencias").json()
    assert "aashto" in ref["ecuaciones"]
