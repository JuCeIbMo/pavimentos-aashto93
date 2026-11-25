"""Memoria de cálculo en PDF (Typst).

Los datos se preparan en Python ya formateados (texto) y se pasan a la plantilla
como `datos.json`; la plantilla nunca interpreta texto del usuario como código Typst.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import tempfile

import typst

from pavimentos.formato import auto, entero, num, pct
from pavimentos.graficos import curva_png, tornado_png
from pavimentos.modelo import ProyectoFlexible
from pavimentos.referencias import REFERENCIAS
from pavimentos.resolver import resolver
from pavimentos.sensibilidad import VARIABLES, barrido, rango_por_defecto, tornado

PLANTILLA = os.path.join(os.path.dirname(__file__), "plantillas", "memoria.typ")

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha(d: _dt.date) -> str:
    return f"{d.day} de {_MESES[d.month - 1]} de {d.year}"


def _md(texto: str) -> str:
    """Quita marcas de Markdown simples de las referencias."""
    return texto.replace("*", "")


def preparar_datos(p: ProyectoFlexible, res: dict, sensibilidad: bool = True) -> tuple[dict, dict]:
    """Devuelve (datos para la plantilla, {nombre_archivo: bytes} de imágenes)."""
    imagenes: dict[str, bytes] = {}
    d: dict = {
        "titulo": p.nombre or "Proyecto sin título",
        "autor": p.autor, "ubicacion": p.ubicacion, "descripcion": p.descripcion,
        "fecha": _fecha(_dt.date.today()),
        "ok": res["ok"],
    }

    tr = res.get("transito")
    if tr:
        d["transito"] = {
            "n": num(tr["n"], 0), "fd": num(tr["fd"], 2), "fc": num(tr["fc"], 2),
            "pt": num(tr["pt_lef"], 1), "sn": num(tr["sn_lef"], 1),
            "tpda": entero(tr["tpda_total"]), "pesados": pct(tr["pesados_pct"]),
            "esal1": entero(tr["esal1_total"]), "w18": entero(tr["w18"]),
            "filas": [[f["nombre"], entero(f["tpda"]), pct(f["r"] * 100), num(f["factor_camion"], 4)
                       + ("" if f["origen_fc"] == "ejes" else " *"), num(f["g"], 3), entero(f["esal1"]),
                       entero(f["w"])] for f in tr["filas"]],
            "hay_dato": any(f["origen_fc"] == "dato" for f in tr["filas"]),
            "unidad_carga": tr["unidad_carga"],
            "conversion": ("" if tr["unidad_carga"] == "kip" else
                           f"Cargas en toneladas convertidas con 1 t = {num(tr['kip_por_t'], 4 if tr['kip_por_t'] != 2 else 0)} kip."),
            "ejes": [[f["nombre"], e["tipo"], num(e["carga"], 2), num(e["carga_kip"], 2), num(e["lef"], 4)]
                     for f in tr["filas"] for e in f["ejes"]],
        }

    sub = res.get("subrasante")
    if sub:
        d["subrasante"] = {
            "filas": [[f["nombre"], num(f["meses"], 1), "—" if f["cbr"] is None else num(f["cbr"], 2),
                       entero(f["mr"]), f["origen"], num(f["uf"], 4), num(f["uf_meses"], 4)]
                      for f in sub["filas"]],
            "suma": num(sub["suma_uf"], 4), "uf_bar": num(sub["uf_bar"], 4),
            "mr_ef": entero(sub["mr_efectivo"]), "mr_prom": entero(sub["mr_promedio"]),
        }

    di = res.get("diseno")
    if di:
        mat = di["materiales"]
        d["diseno"] = {
            "w18": entero(di["w18"]), "fuente_w18": di["fuente_w18"], "log_w18": num(di["log_w18"], 3),
            "mr": entero(di["mr"]), "fuente_mr": di["fuente_mr"],
            "r": pct(di["r_pct"]), "etapas": str(di["etapas"]), "r_etapa": pct(di["r_etapa"], 2),
            "zr": num(di["zr"], 3), "so": num(di["so"], 2), "p0": num(di["p0"], 1), "pt": num(di["pt"], 1),
            "dpsi": num(di["dpsi"], 2), "sn_req": num(di["sn_requerido"], 3), "sn_adop": num(di["sn_adoptado"], 2),
            "materiales": [
                ["Carpeta asfáltica", auto(mat["carpeta"]["e"]), "dato", num(mat["carpeta"]["a"], 4),
                 mat["carpeta"]["origen_a"], "—"],
                ["Base granular", auto(mat["base"]["e"]), mat["base"]["origen_e"], num(mat["base"]["a"], 4),
                 mat["base"]["origen_a"], num(mat["base"]["m"], 2)],
                ["Subbase granular", auto(mat["subbase"]["e"]), mat["subbase"]["origen_e"],
                 num(mat["subbase"]["a"], 4), mat["subbase"]["origen_a"], num(mat["subbase"]["m"], 2)],
            ],
        }

    cl = res.get("clima")
    if cl:
        d["clima"] = {
            "periodo": num(cl["periodo"], 1), "objetivo": num(cl["t_objetivo"], 0),
            "w_adm": entero(cl["w_adm"]), "dpsi_tr": num(cl["dpsi_tr"], 3),
            "vr": num(p.clima.vr, 2), "ps": pct(p.clima.ps, 0), "theta": num(p.clima.theta, 3),
            "helada": p.clima.helada is not None,
            "iter": [[num(i["t"], 2), num(i["dpsi_sw"], 3), num(i["dpsi_fh"], 3), num(i["dpsi_tr"], 3),
                      entero(i["w_adm"]), num(i["t_calc"], 2)] for i in cl["iteraciones"]],
        }

    ca = res.get("capas")
    if ca:
        u = ca["unidad"]
        d["capas"] = {
            "unidad": u, "w": entero(ca["w_diseno"]), "dpsi": num(ca["dpsi_diseno"], 3),
            "sn1": num(ca["sn1"], 3), "sn2": num(ca["sn2"], 3), "sn3": num(ca["sn3"], 3),
            "total": num(ca["sn_total"], 3), "cumple": ca["cumple"], "minimos": ca["origen_minimos"],
            "espesor_total": num(ca["espesor_total"], 1),
            "filas": [[c["capa"], num(c["a"], 4), "—" if c["m"] is None else num(c["m"], 2),
                       num(c["sn_req"], 3), num(c["d_calc"], 2), num(c["d"], 1),
                       num(c["d_cm"], 1) if u == "pulg" else num(c["d_pulg"], 2), num(c["sn_aporte"], 3)]
                      for c in ca["capas"]],
            # espesores numéricos (en cm) para dibujar el esquema a escala
            "dib": [{"nombre": c["capa"], "cm": round(c["d_cm"], 2), "txt": f"{num(c['d'], 1)} {u}"}
                    for c in ca["capas"]],
            "verif": [[v["criterio"], num(v["izq"], 3), num(v["der"], 3), "cumple" if v["cumple"] else "NO cumple"]
                      for v in ca["verificaciones"]],
            "otra_unidad": "cm" if u == "pulg" else "pulg",
        }

    d["decisiones"] = [x["texto"] for x in res["decisiones"]]
    d["avisos"] = [{"nivel": a["nivel"], "texto": a["texto"]} for a in res["avisos"]]
    d["referencias"] = [_md(t) for _, t in REFERENCIAS.items()]

    if sensibilidad and ca and res["ok"]:
        variacion = 0.20
        filas = tornado(p, variacion)
        if filas:
            imagenes["tornado.png"] = tornado_png(filas, variacion)
            d["tornado"] = [[f["etiqueta"], auto(f["x_lo"]), auto(f["x_hi"]), num(f["sn_lo"], 3),
                             num(f["sn_hi"], 3), num(f["esp_lo"], 1), num(f["esp_hi"], 1)] for f in filas]
            d["tornado_top"] = filas[0]["etiqueta"]
        var = VARIABLES["mr"]
        pts = barrido(p, "mr", rango_por_defecto(p, "mr", 21))
        imagenes["curva_mr.png"] = curva_png(pts, f"{var.etiqueta} ({var.unidad})", di["mr"])

    return d, imagenes


def generar_pdf(p: ProyectoFlexible, res: dict | None = None, sensibilidad: bool = True) -> bytes:
    res = res or resolver(p)
    datos, imagenes = preparar_datos(p, res, sensibilidad)
    with tempfile.TemporaryDirectory() as tmp:
        with open(PLANTILLA, encoding="utf-8") as f:
            plantilla = f.read()
        with open(os.path.join(tmp, "memoria.typ"), "w", encoding="utf-8") as f:
            f.write(plantilla)
        with open(os.path.join(tmp, "datos.json"), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
        for nombre, contenido in imagenes.items():
            with open(os.path.join(tmp, nombre), "wb") as f:
                f.write(contenido)
        return typst.compile(os.path.join(tmp, "memoria.typ"))
