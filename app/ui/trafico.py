"""Módulo 1 — Tránsito: ejes equivalentes (ESAL / W18)."""

import pandas as pd
import streamlit as st

from pavimentos.formato import entero, num, pct
from pavimentos.modelo import Vehiculo

from .componentes import avisos, concepto, ecuacion, encabezado, fila_metricas, seccion
from .estado import k, proyecto

CONCEPTO = """
El pavimento no "ve" vehículos: ve **repeticiones de carga por eje**. Para sumar ejes de pesos
distintos, AASHTO los convierte a un eje patrón de **18 kip (8,2 t) en eje simple** mediante el
**factor de equivalencia de carga (LEF)**. El daño crece aproximadamente con la **cuarta potencia**
de la carga: un eje de 16,4 t no daña el doble que uno de 8,2 t, sino unas 16 veces más.

- **Factor de camión (FC):** suma de los LEF de todos los ejes de un vehículo.
- **ESAL del año 1:** TPDA × FC × 365 × F<sub>d</sub> × F<sub>c</sub> (solo el carril de diseño).
- **W<sub>18</sub>:** ESAL acumulados en el período, con crecimiento compuesto.

Los LEF dependen un poco del SN y de p<sub>t</sub> (que todavía no se conocen): se supone un SN y se
verifica al final. Si el SN resultante es muy distinto, el programa avisa.
"""

AYUDA = {
    "n": "Años de servicio que debe cubrir esta etapa. AASHTO recomienda 10–20 años para la etapa inicial.",
    "fd": "Fracción del tránsito total que va en la dirección más cargada. Normalmente 0,5 (rango 0,3–0,7).",
    "fc": "Fracción de los vehículos de esa dirección que circula por el carril de diseño: "
          "1 carril → 1,0 · 2 carriles → 0,80–1,00 · 3 carriles → 0,60–0,80 · 4 o más → 0,50–0,75.",
    "pt": "Serviciabilidad terminal con la que se leen las tablas LEF (2,0; 2,5 o 3,0). Conviene igualarla al pt de diseño.",
    "sn": "SN supuesto para leer los LEF. Se estima y luego se compara con el SN obtenido en el módulo 4.",
}

COLUMNAS = {
    "nombre": st.column_config.TextColumn("Vehículo", width="medium"),
    "tpda": st.column_config.NumberColumn("TPDA (veh/día)", min_value=0, format="%.0f"),
    "r_pct": st.column_config.NumberColumn("Crecimiento r (%)", min_value=0, max_value=20, format="%.2f"),
    "pesado": st.column_config.CheckboxColumn("Pesado"),
    "ejes": st.column_config.TextColumn(
        "Ejes (tipo carga_t; …)", width="large",
        help="Ej.: «simple 7; tandem 18». Tipos: simple, tandem, tridem. Cargas en toneladas."),
    "fc_dato": st.column_config.NumberColumn(
        "Factor de camión conocido", min_value=0, format="%.4f",
        help="Opcional. Si lo cargás, reemplaza al cálculo por ejes (dato de pesaje o de la fuente)."),
}


def _ejes_a_str(ejes):
    return "; ".join(f"{t} {num(c, 1).replace(',', '.')}" for t, c in ejes)


def _str_a_ejes(s):
    out = []
    for parte in str(s or "").replace(",", ";").split(";"):
        parte = parte.strip()
        if not parte:
            continue
        tipo, carga = parte.split()
        tipo = tipo.lower()
        if tipo not in ("simple", "tandem", "tridem"):
            raise ValueError(f"tipo de eje «{tipo}»")
        out.append([tipo, float(carga)])
    return out


def _df(vehiculos):
    return pd.DataFrame([{
        "nombre": v.nombre, "tpda": v.tpda, "r_pct": v.r * 100, "pesado": v.pesado,
        "ejes": _ejes_a_str(v.ejes), "fc_dato": v.factor_camion,
    } for v in vehiculos], columns=list(COLUMNAS))


def render(res: dict):
    p = proyecto()
    t = p.transito
    encabezado("Cálculo de ejes equivalentes",
               "Convierte el TPDA y la composición vehicular en repeticiones del eje patrón de 18 kip.",
               badge="01")
    concepto("¿Qué es un eje equivalente y por qué importa?", CONCEPTO)

    seccion("Parámetros del tránsito")
    c = st.columns(5)
    t.n = c[0].number_input("Período n (años)", 1.0, 50.0, float(t.n), 1.0, key=k("t_n"), help=AYUDA["n"])
    t.fd = c[1].number_input("Distribución direccional Fd", 0.1, 1.0, float(t.fd), 0.05, key=k("t_fd"), help=AYUDA["fd"])
    t.fc = c[2].number_input("Distribución por carril Fc", 0.1, 1.0, float(t.fc), 0.05, key=k("t_fc"), help=AYUDA["fc"])
    opciones_pt = [2.0, 2.5, 3.0]
    t.pt = c[3].selectbox("pt para LEF", opciones_pt, index=opciones_pt.index(t.pt) if t.pt in opciones_pt else 0,
                          key=k("t_pt"), help=AYUDA["pt"])
    t.sn_lef = c[4].number_input("SN supuesto (LEF)", 1.0, 6.0, float(t.sn_lef), 0.5, key=k("t_sn"), help=AYUDA["sn"])

    seccion("Composición vehicular",
            "Editá la tabla directamente; podés agregar o borrar filas. Si conocés el factor de camión, "
            "cargalo y se ignoran los ejes de esa fila.")
    fuente = st.session_state.setdefault(k("veh_df"), _df(t.vehiculos))
    editado = st.data_editor(fuente, num_rows="dynamic", width="stretch", hide_index=True,
                             column_config=COLUMNAS, key=k("veh_editor"))
    vehiculos, errores = [], []
    for _, fila in editado.iterrows():
        if not str(fila.get("nombre") or "").strip() and pd.isna(fila.get("tpda")):
            continue
        try:
            ejes = _str_a_ejes(fila.get("ejes"))
        except Exception as e:  # noqa: BLE001
            errores.append(f"«{fila.get('nombre')}»: ejes mal escritos ({e}). Formato: simple 7; tandem 18")
            ejes = []
        fc_dato = fila.get("fc_dato")
        fc_dato = None if fc_dato is None or pd.isna(fc_dato) else float(fc_dato)
        if not ejes and fc_dato is None:
            errores.append(f"«{fila.get('nombre')}»: faltan ejes o factor de camión.")
            continue
        vehiculos.append(Vehiculo(
            nombre=str(fila.get("nombre") or "Vehículo"), tpda=float(fila.get("tpda") or 0),
            r=float(fila.get("r_pct") or 0) / 100, pesado=bool(fila.get("pesado")),
            ejes=ejes, factor_camion=fc_dato))
    t.vehiculos = vehiculos
    for e in errores:
        st.warning(e)

    tr = res.get("transito")
    avisos(res, "transito")
    if not tr:
        st.info("Cargá al menos un vehículo para calcular el tránsito.")
        return

    seccion("Resultados")
    fila_metricas([
        {"etiqueta": "W18 de diseño", "valor": entero(tr["w18"]), "sub": f"ESAL en {num(t.n, 0)} años, carril de diseño"},
        {"etiqueta": "ESAL del primer año", "valor": entero(tr["esal1_total"]), "sub": "carril de diseño"},
        {"etiqueta": "TPDA total", "valor": entero(tr["tpda_total"]), "sub": "veh/día, ambos sentidos"},
        {"etiqueta": "Vehículos pesados", "valor": pct(tr["pesados_pct"]), "sub": "del TPDA"},
    ])
    df = pd.DataFrame([{
        "Vehículo": f["nombre"], "TPDA": f["tpda"], "r (%)": f["r"] * 100,
        "FC": f["factor_camion"], "Origen FC": "Σ LEF de ejes" if f["origen_fc"] == "ejes" else "dato",
        "G": f["g"], "ESAL año 1": f["esal1"], "W": f["w"], "% de W18": 100 * f["w"] / tr["w18"],
    } for f in tr["filas"]])
    st.dataframe(df, hide_index=True, width="stretch", column_config={
        "TPDA": st.column_config.NumberColumn(format="%.0f"), "r (%)": st.column_config.NumberColumn(format="%.2f"),
        "FC": st.column_config.NumberColumn(format="%.4f"), "G": st.column_config.NumberColumn(format="%.3f"),
        "ESAL año 1": st.column_config.NumberColumn(format="%.0f"), "W": st.column_config.NumberColumn(format="%.0f"),
        "% de W18": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
    })
    pesados = sorted(tr["filas"], key=lambda f: f["w"], reverse=True)[:2]
    st.caption(f"💡 Observá la columna «% de W18»: «{pesados[0]['nombre']}» aporta el "
               f"{num(100 * pesados[0]['w'] / tr['w18'], 1)} % del daño. Los autos casi no cuentan, "
               "aunque sean mayoría en el TPDA.")

    ejes = [{"Vehículo": f["nombre"], "Eje": e["tipo"], "Carga (t)": e["carga_t"], "Carga (kip)": e["carga_kip"],
             "LEF": e["lef"]} for f in tr["filas"] for e in f["ejes"]]
    if ejes:
        with st.expander("Detalle de LEF por eje (Apéndice D de AASHTO)"):
            st.dataframe(pd.DataFrame(ejes), hide_index=True, width="stretch",
                         column_config={"LEF": st.column_config.NumberColumn(format="%.4f")})

    with st.expander("📐 Procedimiento y ecuaciones", expanded=False):
        ecuacion("lef")
        ecuacion("crecimiento")
        ecuacion("esal")
