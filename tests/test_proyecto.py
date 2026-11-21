import json

from pavimentos.proyecto import Proyecto, cargar_proyecto, guardar_proyecto
from pavimentos.reporte import generar_reporte_html


def test_guardar_cargar_roundtrip(tmp_path):
    p = Proyecto(nombre="Prueba", trafico={"total_w": 890521}, subrasante={"mr_efectivo": 10222})
    path = tmp_path / "p.json"
    guardar_proyecto(p, str(path))
    q = cargar_proyecto(str(path))
    assert q.nombre == "Prueba"
    assert q.trafico["total_w"] == 890521
    assert q.subrasante["mr_efectivo"] == 10222


def test_reporte_html():
    p = Proyecto(nombre="Prueba")
    html = generar_reporte_html(p, {"trafico": {"total_w": 890521}})
    assert "<html" in html and "890" in html and "<table" in html
