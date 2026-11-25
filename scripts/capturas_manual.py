"""Capturas de la interfaz para el manual de usuario.

Abre la app en un Chromium sin ventana, con el proyecto inicial (navegador limpio),
recorre cada módulo y guarda una imagen por tarjeta o sección.

Uso (con la app corriendo en http://localhost:5173):
    uv run --with playwright python scripts/capturas_manual.py CARPETA_DESTINO
"""

import re
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

URL = "http://localhost:5173"
CHROMIUM = "/usr/bin/chromium"
SIN_BARRA_FIJA = ".sticky{position:static!important}"


def ir(pg: Page, pagina: str):
    pg.goto(f"{URL}/#/{pagina}")
    pg.wait_for_timeout(1500)


def tarjeta(pg: Page, titulo: str):
    return pg.locator("section").filter(
        has=pg.get_by_role("heading", name=re.compile("^" + re.escape(titulo)))).first


def grilla_de(pg: Page, texto: str):
    """Fila de KPIs que contiene la etiqueta dada."""
    etiqueta = pg.locator("div.uppercase").filter(has_text=re.compile("^" + re.escape(texto) + "$")).first
    return etiqueta.locator("xpath=ancestor::div[contains(@class,'grid')][1]")


def foto(loc, out: Path, nombre: str):
    loc.scroll_into_view_if_needed()
    loc.page.wait_for_timeout(250)
    loc.screenshot(path=str(out / f"{nombre}.png"), animations="disabled")
    print("ok", nombre)


def concepto(pg: Page, titulo: str):
    boton = pg.get_by_role("button", name=re.compile(re.escape(titulo)))
    boton.click()
    pg.wait_for_timeout(300)
    return boton.locator("xpath=..")


def ecuaciones(pg: Page):
    boton = pg.get_by_role("button", name=re.compile("Procedimiento y ecuaciones"))
    boton.click()
    pg.wait_for_timeout(600)
    return boton.locator("xpath=..")


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROMIUM)
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5, locale="es-AR")
        pg = ctx.new_page()

        # ---------------------------------------------------------- vista general
        ir(pg, "transito")
        pg.screenshot(path=str(out / "general-pantalla.png"))
        foto(pg.locator("div.sticky").first, out, "general-barra-superior")
        foto(pg.locator("aside").first if pg.locator("aside").count() else pg.locator("nav").first, out, "general-menu")
        pg.add_style_tag(content=SIN_BARRA_FIJA)

        # ---------------------------------------------------------- inicio
        ir(pg, "inicio")
        pg.add_style_tag(content=SIN_BARRA_FIJA)
        foto(pg.get_by_text("Flujo de cálculo", exact=True).locator("xpath=.."), out, "inicio-flujo")
        foto(tarjeta(pg, "Datos del proyecto"), out, "inicio-datos")
        foto(tarjeta(pg, "Empezar desde un ejemplo"), out, "inicio-ejemplos")

        # ---------------------------------------------------------- módulo 1
        ir(pg, "transito")
        pg.add_style_tag(content=SIN_BARRA_FIJA)
        foto(concepto(pg, "¿Qué es un eje equivalente"), out, "m1-concepto")
        foto(tarjeta(pg, "Parámetros del tránsito"), out, "m1-parametros")
        foto(tarjeta(pg, "Composición vehicular"), out, "m1-composicion")
        foto(grilla_de(pg, "W18 de diseño"), out, "m1-kpis")
        foto(tarjeta(pg, "Resultado: ejes equivalentes por vehículo"), out, "m1-resultados")
        foto(tarjeta(pg, "Decisiones de diseño"), out, "m1-decisiones")
        foto(ecuaciones(pg), out, "m1-ecuaciones")

        # menú de agregar y fila incompleta
        comp = tarjeta(pg, "Composición vehicular")
        comp.get_by_role("button", name=re.compile("Agregar vehículo")).click()
        pg.wait_for_timeout(300)
        menu = comp.get_by_text("Fila vacía", exact=True).locator("xpath=..")
        foto(menu, out, "m1-agregar-menu")
        comp.get_by_role("button", name="Simple + tándem", exact=True).click()
        pg.wait_for_timeout(1200)
        pg.evaluate("window.scrollTo(0, 0)")
        caja = comp.bounding_box()
        alto = 520
        pg.screenshot(path=str(out / "m1-fila-incompleta.png"), full_page=True,
                      clip={"x": caja["x"], "y": caja["y"] + caja["height"] - alto, "width": caja["width"], "height": alto})
        print("ok m1-fila-incompleta")
        # factor camión dado en la primera fila
        comp.get_by_role("button", name="usar valor dado").first.click()
        pg.wait_for_timeout(200)
        campo = comp.get_by_placeholder("factor…").first
        campo.fill("2,1")
        pg.wait_for_timeout(1200)
        pg.evaluate("window.scrollTo(0, 0)")
        caja = comp.bounding_box()
        pg.screenshot(path=str(out / "m1-factor-dado.png"), full_page=True,
                      clip={"x": caja["x"], "y": caja["y"], "width": caja["width"], "height": 290})
        print("ok m1-factor-dado")

        # proyecto limpio de nuevo: contexto nuevo (almacenamiento vacío)
        ctx.close()
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5, locale="es-AR")
        pg = ctx.new_page()
        ir(pg, "subrasante")
        pg.add_style_tag(content=SIN_BARRA_FIJA)

        # ---------------------------------------------------------- módulo 2
        foto(concepto(pg, "¿Por qué un MR"), out, "m2-concepto")
        foto(tarjeta(pg, "Variación estacional"), out, "m2-tabla")
        foto(grilla_de(pg, "MR efectivo"), out, "m2-kpis")
        foto(tarjeta(pg, "¿Qué período daña más?"), out, "m2-grafico")
        foto(tarjeta(pg, "Decisiones de diseño"), out, "m2-decisiones")

        # ---------------------------------------------------------- módulo 4
        ir(pg, "diseno")
        pg.add_style_tag(content=SIN_BARRA_FIJA)
        foto(concepto(pg, "¿Cómo funciona la ecuación"), out, "m4-concepto")
        foto(tarjeta(pg, "Tránsito de diseño W18").locator("xpath=.."), out, "m4-fuentes")
        foto(tarjeta(pg, "Confiabilidad y serviciabilidad"), out, "m4-confiabilidad")
        mat = tarjeta(pg, "Materiales")
        foto(mat, out, "m4-materiales")
        mat.locator("summary").filter(has_text="Asistente de drenaje").click()
        pg.wait_for_timeout(400)
        foto(mat, out, "m4-drenaje")
        mat.locator("summary").filter(has_text="Asistente de drenaje").click()
        foto(tarjeta(pg, "Criterios de redondeo y espesores mínimos"), out, "m4-criterios")
        foto(grilla_de(pg, "SN requerido"), out, "m4-kpis")
        foto(tarjeta(pg, "Estructura adoptada").locator("xpath=.."), out, "m4-estructura")
        foto(tarjeta(pg, "Decisiones de diseño"), out, "m4-decisiones")

        # ---------------------------------------------------------- módulo 6
        ir(pg, "clima")
        pg.add_style_tag(content=SIN_BARRA_FIJA)
        foto(concepto(pg, "¿Cómo afecta el clima"), out, "m6-concepto")
        foto(pg.get_by_text("Considerar efectos ambientales en el diseño").locator("xpath=ancestor::section[1]"), out, "m6-activar")
        foto(tarjeta(pg, "Hinchamiento (suelos expansivos)").locator("xpath=.."), out, "m6-datos")
        foto(grilla_de(pg, "Período de desempeño"), out, "m6-kpis")
        foto(tarjeta(pg, "Iteraciones").locator("xpath=.."), out, "m6-iteraciones")

        # ---------------------------------------------------------- sensibilidad
        ir(pg, "sensibilidad")
        pg.add_style_tag(content=SIN_BARRA_FIJA)
        principal = pg.locator("main").first
        pg.wait_for_timeout(800)
        foto(principal, out, "sens-curva")
        pg.get_by_role("button", name="Tornado", exact=True).click()
        pg.wait_for_timeout(1500)
        foto(principal, out, "sens-tornado")
        pg.get_by_role("button", name="Escenarios", exact=True).click()
        pg.wait_for_timeout(1500)
        foto(principal, out, "sens-escenarios")

        # ---------------------------------------------------------- validación y referencias
        ir(pg, "validacion")
        pg.add_style_tag(content=SIN_BARRA_FIJA)
        pg.wait_for_timeout(800)
        foto(grilla_de(pg, "Ejercicios aprobados"), out, "val-kpis")
        primero = pg.get_by_role("button", name=re.compile("Práctico 3")).first
        primero.click()
        pg.wait_for_timeout(500)
        foto(primero.locator("xpath=.."), out, "val-ejercicio")
        ir(pg, "referencias")
        pg.add_style_tag(content=SIN_BARRA_FIJA)
        foto(tarjeta(pg, "Bibliografía"), out, "ref-bibliografia")

        b.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
