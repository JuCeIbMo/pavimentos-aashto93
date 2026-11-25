"""Validación del paquete contra ejercicios resueltos de la cátedra y de la bibliografía."""

import pandas as pd
import streamlit as st

from pavimentos.exportar_pdf import generar_pdf
from pavimentos.formato import auto, num
from pavimentos.validacion import validar_todo

from .componentes import concepto, encabezado, fila_metricas
from .estado import reemplazar

CONCEPTO = """
Un programa de diseño solo es confiable si reproduce resultados conocidos. Cada ejercicio de
esta página está guardado como un **proyecto completo**: el programa lo resuelve desde cero y
compara cada valor intermedio y final con el de la fuente.

- **Diferencia %**: (app − fuente) / fuente. Diferencias pequeñas son esperables cuando la fuente
  redondea (por ejemplo, Z<sub>R</sub> = −1,405 en lugar de −1,418) o lee un nomograma.
- **Informativo**: comparaciones que se muestran pero no cuentan como falla, porque la diferencia
  viene de un error de la propia fuente (el programa lo detecta y lo explica).

Podés **cargar cualquier ejercicio** en la app para recorrerlo módulo por módulo o exportar su PDF.
"""


@st.cache_data(show_spinner=False)
def _validar():
    out = []
    for v in validar_todo():
        out.append({**v, "proyecto_json": v["proyecto"].to_json(), "proyecto": None, "resultado": None})
    return out


def render(res: dict):
    encabezado("Validación del paquete",
               "Cuatro ejercicios resueltos de fuentes independientes, comparados valor por valor.", badge="✓")
    concepto("¿Cómo se valida el programa?", CONCEPTO)

    resultados = _validar()
    total_ok = sum(v["n_ok"] for v in resultados)
    total = sum(v["n_total"] for v in resultados)
    fila_metricas([
        {"etiqueta": "Ejercicios aprobados", "valor": f"{sum(v['aprobado'] for v in resultados)} / {len(resultados)}",
         "sub": "cátedra + bibliografía"},
        {"etiqueta": "Comparaciones dentro de tolerancia", "valor": f"{total_ok} / {total}", "sub": "valores intermedios y finales"},
        {"etiqueta": "Mayor diferencia", "valor": num(max(abs(f["dif_rel"]) * 100 for v in resultados for f in v["filas"]
                                                          if f.get("tipo") != "informativo" and f["dif_rel"] is not None), 2) + " %",
         "sub": "entre valores comparados"},
    ])

    from pavimentos.modelo import ProyectoFlexible
    for v in resultados:
        f = v["fuente"]
        icono = "✅" if v["aprobado"] else "❌"
        with st.expander(f"{icono} **{f['titulo']}** · {f['tipo']} · {v['n_ok']}/{v['n_total']} valores", expanded=False):
            st.caption(f"📖 {f['referencia']}")
            proyecto = ProyectoFlexible.from_json(v["proyecto_json"])
            if proyecto.descripcion:
                st.markdown(proyecto.descripcion)
            df = pd.DataFrame([{
                "": ("✅" if x["cumple"] else ("ℹ️" if x.get("tipo") == "informativo" else "❌")),
                "Valor": x["etiqueta"], "Unidad": x.get("unidad", ""),
                "Fuente": auto(x["valor"]), "App": auto(x["app"]),
                "Diferencia": "—" if x["dif_rel"] is None else f"{num(x['dif_rel'] * 100, 2)} %",
                "Tolerancia": f"± {num(x['tol_rel'] * 100, 1)} %", "Nota": x.get("nota", ""),
            } for x in v["filas"]])
            st.dataframe(df, hide_index=True, width="stretch",
                         column_config={"Nota": st.column_config.TextColumn(width="large")})
            notas = [x for x in v["filas"] if x.get("tipo") == "informativo" and not x["cumple"]]
            if notas:
                st.warning("**Discrepancias atribuibles a la fuente** (no cuentan como falla):\n\n" +
                           "\n".join(f"- {x['etiqueta']}: {x['nota'] or 'diferencia por redondeos de la fuente.'}"
                                     for x in notas))
            c1, c2 = st.columns(2)
            if c1.button("Cargar este ejercicio en la app", key=f"cargar_{v['id']}", width="stretch"):
                reemplazar(proyecto)
                st.session_state["pagina_actual"] = "Inicio"
                st.rerun()
            if c2.button("Preparar PDF de este ejercicio", key=f"pdf_{v['id']}", width="stretch"):
                st.session_state[f"pdf_val_{v['id']}"] = generar_pdf(proyecto)
            if st.session_state.get(f"pdf_val_{v['id']}"):
                c2.download_button("⬇ Descargar PDF", st.session_state[f"pdf_val_{v['id']}"],
                                   file_name=f"validacion_{v['id']}.pdf", mime="application/pdf",
                                   key=f"dl_{v['id']}", width="stretch")
