import io

import openpyxl
import pytest

from pavimentos.exportar_excel import generar_excel
from pavimentos.exportar_pdf import generar_pdf, preparar_datos
from pavimentos.modelo import ProyectoFlexible
from pavimentos.resolver import resolver
from pavimentos.sensibilidad import barrido, comparar_escenarios, tornado
from pavimentos.validacion import listar

EJ = listar()


@pytest.mark.parametrize("ej", EJ, ids=[e["id"] for e in EJ])
def test_pdf_se_genera(ej):
    p = ProyectoFlexible.from_dict(ej["proyecto"])
    pdf = generar_pdf(p)
    assert pdf[:4] == b"%PDF" and len(pdf) > 20_000


def test_pdf_con_proyecto_incompleto_no_explota():
    p = ProyectoFlexible()
    res = resolver(p)
    datos, _ = preparar_datos(p, res)
    assert datos["avisos"]
    assert generar_pdf(p, res)[:4] == b"%PDF"


@pytest.mark.parametrize("ej", EJ, ids=[e["id"] for e in EJ])
def test_excel_tiene_formulas_vivas(ej):
    p = ProyectoFlexible.from_dict(ej["proyecto"])
    wb = openpyxl.load_workbook(io.BytesIO(generar_excel(p)))
    assert wb.sheetnames[0] == "Resumen"
    assert "SN (biseccion)" in wb.sheetnames
    formulas = [c.value for ws in wb for row in ws.iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith("=")]
    assert len(formulas) > 200
    assert any("LOG10" in f and "5.19" in f for f in formulas)


def test_tornado_ordenado_y_escenarios():
    p = ProyectoFlexible.from_dict(EJ[1]["proyecto"])
    t = tornado(p)
    assert t and all(t[i]["rango_sn"] >= t[i + 1]["rango_sn"] for i in range(len(t) - 1))
    q = p.copia()
    q.diseno.r_pct = 95
    filas = comparar_escenarios([("Base", p), ("R = 95 %", q)])
    assert filas[1]["sn_requerido"] > filas[0]["sn_requerido"]
    b = barrido(p, "mr", [4000, 8000])
    assert b[0]["sn_requerido"] > b[1]["sn_requerido"]
