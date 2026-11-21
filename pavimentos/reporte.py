"""Reporte HTML autocontenido e imprimible (A4)."""

from html import escape


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:,.3f}".replace(",", "\u00a0") if abs(v) >= 1000 else f"{v:.3f}"
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return escape(str(v))


def _tabla(titulo: str, datos: dict) -> str:
    filas = "".join(
        f"<tr><th>{escape(str(k))}</th><td>{_fmt(v)}</td></tr>"
        for k, v in datos.items()
    )
    return (
        f"<h2>{escape(titulo)}</h2>"
        f"<table><tbody>{filas}</tbody></table>"
    )


def generar_reporte_html(proyecto, resultados: dict) -> str:
    """Genera un HTML autocontenido con las secciones de resultados."""
    secciones = "".join(_tabla(titulo, datos) for titulo, datos in resultados.items())
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{escape(proyecto.nombre)}</title>
<style>
  body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ border-bottom: 2px solid #333; padding-bottom: .5rem; }}
  h2 {{ margin-top: 1.5rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: .4rem .6rem; text-align: left; }}
  th {{ background: #f0f0f0; width: 40%; }}
  @media print {{ body {{ max-width: none; }} }}
</style>
</head>
<body>
<h1>{escape(proyecto.nombre)}</h1>
<p>Diseño de pavimento flexible — AASHTO 1993</p>
{secciones}
</body>
</html>
"""
