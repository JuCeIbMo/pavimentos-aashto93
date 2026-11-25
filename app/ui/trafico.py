"""Módulo 1 — Tránsito: ejes equivalentes (ESAL / W18)."""

import pandas as pd
import streamlit as st

from pavimentos import catalogo
from pavimentos.formato import entero, num
from pavimentos.modelo import KIP_POR_T_CATEDRA, KIP_POR_T_EXACTO, Vehiculo

from .componentes import avisos, concepto, decisiones, ecuacion, encabezado, fila_metricas, seccion
from .estado import k, proyecto, refrescar

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

EJES = ["simple", "tandem", "tridem"]
NOMBRE_EJE = {"simple": "Simple", "tandem": "Tándem", "tridem": "Trídem"}
POSICION = ["Eje delantero", "Eje trasero 1", "Eje trasero 2", "Eje trasero 3", "Eje trasero 4", "Eje trasero 5"]


CSS_TABLA = """
<style>
.st-key-tabla_veh [data-testid="stNumberInputStepUp"],
.st-key-tabla_veh [data-testid="stNumberInputStepDown"] { display: none !important; }
.st-key-tabla_veh, .st-key-tabla_veh [data-testid="stVerticalBlock"] { gap: 3px !important; }
.st-key-tabla_veh .react-aria-ComboBox > div { height: 30px !important; min-height: 30px !important; }
.st-key-tabla_veh .react-aria-ComboBox input { height: 28px !important; font-size: 13px !important;
    text-align: left; padding: 0 0 0 6px !important; }
.st-key-tabla_veh [data-testid="stHorizontalBlock"] { gap: 4px !important; align-items: center; }
.st-key-tabla_veh [data-testid="stNumberInputContainer"],
.st-key-tabla_veh [data-testid="stTextInputRootElement"],
.st-key-tabla_veh [data-baseweb="input"],
.st-key-tabla_veh [data-baseweb="base-input"] { height: 30px !important; min-height: 30px !important; }
.st-key-tabla_veh input { padding: 0 6px !important; font-size: 13.5px !important; text-align: right; }
.st-key-tabla_veh [data-testid="stTextInput"] input { text-align: left; }
.st-key-tabla_veh [data-baseweb="select"] > div { height: 30px !important; min-height: 30px !important;
    font-size: 13px !important; padding-left: 2px !important; }
.st-key-tabla_veh [data-baseweb="select"] > div > div { padding-top: 0 !important; padding-bottom: 0 !important; }
.st-key-tabla_veh button { min-height: 30px !important; height: 30px; padding: 0 !important; }
.veh-head { font-size: 12px; font-weight: 600; color: #6b7280; text-align: center;
            line-height: 1.15; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px; margin-bottom: 6px; }
.veh-head.izq { text-align: left; }
.veh-num { font-weight: 600; color: #9ca3af; text-align: center; font-size: 13px; }
.veh-sep { border-bottom: 1px solid #eef0f3; margin: 1px 0 3px; }
</style>
"""
ANCHOS = [0.3, 2.2, 1, 1, 1, 1, 0.85, 0.75, 0.85, 0.35]


def _cabecera(u):
    c = st.columns(ANCHOS)
    titulos = ["#", "Vehículo"] + [f"{p}<br>({u})" for p in POSICION[:4]] + ["Vehículos<br>actuales (TPDA)",
                                                                             "Tasa<br>crec. (%)", "FC dato<br>(opcional)", ""]
    for col, tit in zip(c, titulos):
        col.markdown(f"<div class='veh-head{' izq' if tit == 'Vehículo' else ''}'>{tit}</div>", unsafe_allow_html=True)


def _fila(i, v, u):
    c = st.columns(ANCHOS)
    c[0].markdown(f"<div class='veh-num'>{i + 1}</div>", unsafe_allow_html=True)
    v.nombre = c[1].text_input("Vehículo", v.nombre, key=k(f"v{i}_nom"), label_visibility="collapsed") or "Vehículo"
    ejes = list(v.ejes) + [[None, None]] * (4 - len(v.ejes))
    nuevos = []
    for j in range(4):
        tipo, carga = ejes[j]
        with c[2 + j]:
            carga = st.number_input("Carga", min_value=0.0, value=float(carga) if carga else None, step=0.5,
                                    format="%.2f", key=k(f"v{i}_e{j}_c"), label_visibility="collapsed",
                                    placeholder="—")
            tipo = st.selectbox("Tipo", EJES, EJES.index(tipo) if tipo in EJES else None,
                                format_func=NOMBRE_EJE.get, key=k(f"v{i}_e{j}_t"),
                                label_visibility="collapsed", placeholder="—")
        if carga or tipo:
            nuevos.append([tipo or "simple", float(carga or 0.0)])
    v.ejes = nuevos + [list(e) for e in v.ejes[4:]]  # ejes extra (>4) de proyectos guardados se conservan
    v.tpda = c[6].number_input("TPDA", min_value=0.0, value=float(v.tpda), step=1.0, format="%.0f",
                               key=k(f"v{i}_tpda"), label_visibility="collapsed")
    v.r = c[7].number_input("r", min_value=0.0, max_value=20.0, value=float(v.r * 100), step=0.25, format="%.2f",
                            key=k(f"v{i}_r"), label_visibility="collapsed") / 100
    fc = c[8].number_input("FC", min_value=0.0, value=v.factor_camion, step=0.01, format="%.4f",
                           key=k(f"v{i}_fc"), label_visibility="collapsed", placeholder="—",
                           help="Factor de camión conocido (pesaje o enunciado). Si lo cargás, se ignoran los ejes.")
    v.factor_camion = fc
    c[9].button("🗑", key=k(f"v{i}_del"), on_click=_borrar, args=(i,), help="Borrar vehículo")
    st.markdown("<div class='veh-sep'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- callbacks
def _cambiar_unidad(clave):
    t = proyecto().transito
    nueva = st.session_state[clave]
    if nueva != t.unidad_carga:
        f = t.kip_por_t if nueva == "kip" else 1 / t.kip_por_t
        for v in t.vehiculos:
            v.ejes = [[tipo, round(c * f, 3)] for tipo, c in v.ejes]
        t.unidad_carga = nueva
        refrescar()


def _agregar(plantilla):
    t = proyecto().transito
    f = t.kip_por_t if plantilla["unidad"] == "t" and t.unidad_carga == "kip" else 1.0
    t.vehiculos.append(Vehiculo(nombre=plantilla["nombre"], pesado=plantilla["pesado"],
                                ejes=[[tipo, round(c * f, 3)] for tipo, c in plantilla["ejes"]]))
    refrescar()


def _borrar(i):
    del proyecto().transito.vehiculos[i]
    refrescar()


def _fila_vacia():
    proyecto().transito.vehiculos.append(Vehiculo(nombre=f"Vehículo {len(proyecto().transito.vehiculos) + 1}"))
    refrescar()


def _agregar_elegido(clave, opciones):
    _agregar(dict(opciones)[st.session_state[clave]])


def _agregar_practico():
    for _, pl in catalogo.opciones():
        if pl["fuente"]:
            _agregar(pl)


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

    c = st.columns([1, 2])
    c[0].radio("Cargas por eje en", ["t", "kip"], ["t", "kip"].index(t.unidad_carga), horizontal=True,
               format_func={"t": "toneladas", "kip": "kip"}.get, key=k("t_uc"),
               on_change=_cambiar_unidad, args=(k("t_uc"),),
               help="Al cambiar de unidad, las cargas ya cargadas se convierten solas.")
    if t.unidad_carga == "t":
        modos = [KIP_POR_T_EXACTO, KIP_POR_T_CATEDRA]
        actual = 1 if abs(t.kip_por_t - KIP_POR_T_CATEDRA) < 1e-9 else 0
        t.kip_por_t = c[1].radio(
            "Conversión a kip", modos, actual, horizontal=True, key=k("t_conv"),
            format_func=lambda x: "exacta (1 t = 2,2046 kip)" if x == KIP_POR_T_EXACTO else "cátedra (1 t = 2 kip)",
            help="Las tablas LEF están en kip. La exacta es 1 t = 1000 kg = 2204,6 lb. "
                 "En clase se usa ×2 para leer las tablas a mano; el Práctico 3 está resuelto así.")
    else:
        c[1].caption("Las cargas se usan tal cual en las tablas AASHTO (en kip).")

    seccion("Composición vehicular",
            "Cada vehículo con su TPDA, su tasa de crecimiento y sus ejes. Las tablas LEF se leen "
            "por tipo de eje y carga en kip; el nombre del vehículo es solo una etiqueta.")
    st.markdown(CSS_TABLA, unsafe_allow_html=True)
    with st.container(key="tabla_veh"):
        _cabecera("t" if t.unidad_carga == "t" else "kip")
        for i, v in enumerate(list(t.vehiculos)):
            _fila(i, v, t.unidad_carga)
    st.caption("En cada eje: carga arriba y tipo abajo (simple, tándem o trídem). Dejá vacío un eje que el "
               "vehículo no tiene. Si cargás el FC dato, se usa ese factor y se ignoran los ejes.")

    opciones = catalogo.opciones()
    c = st.columns([4, 1, 1.6, 1], vertical_alignment="bottom")
    c[3].button("＋ Fila vacía", key=k("add_vacia"), on_click=_fila_vacia, width="stretch")
    c[0].selectbox("Agregar vehículo", [o[0] for o in opciones], key=k("add_sel"),
                   help="📘 = tabla de vehículos del Práctico 3 (cátedra), con sus cargas. "
                        "⚙️ = solo la configuración de ejes; las cargas las escribís vos.")
    c[1].button("＋ Agregar", key=k("add_btn"), on_click=_agregar_elegido, args=(k("add_sel"), opciones),
                width="stretch")
    c[2].button("📘 Agregar toda la tabla del Práctico 3", key=k("add_all"), on_click=_agregar_practico,
                width="stretch")
    st.caption(f"📘 Fuente de las cargas: {catalogo.FUENTE_PRACTICO3}. TPDA y r quedan en cero para completar.")

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

    lectura = []
    for f in tr["filas"]:
        if not f["ejes"]:
            continue
        fila = {"Vehículo": f["nombre"]}
        for j, e in enumerate(f["ejes"]):
            pos = POSICION[j] if j < len(POSICION) else f"Eje {j + 1}"
            fila[pos] = f"{NOMBRE_EJE[e['tipo']]} {num(e['carga_kip'], 2)} kip → {num(e['lef'], 4)}"
        fila["FC = Σ LEF"] = f["factor_camion"]
        lectura.append(fila)
    if lectura:
        seccion("Lectura de las tablas LEF",
                f"Cada eje: tipo y carga en kip con la que se entra a la tabla AASHTO (pt = {num(t.pt, 1)}, "
                f"SN = {num(t.sn_lef, 1)}) → LEF leído. El factor de camión es la suma de la fila.")
        m = max(len(f["ejes"]) for f in tr["filas"])
        orden = ["Vehículo"] + [POSICION[j] if j < len(POSICION) else f"Eje {j + 1}" for j in range(m)] + ["FC = Σ LEF"]
        st.dataframe(pd.DataFrame(lectura, columns=orden).fillna(""), hide_index=True, width="stretch",
                     height=36 * (len(lectura) + 1) + 4,
                     column_config={"FC = Σ LEF": st.column_config.NumberColumn(format="%.4f")})
    decisiones(res, "transito")

    with st.expander("📐 Procedimiento y ecuaciones", expanded=False):
        ecuacion("lef")
        ecuacion("crecimiento")
        ecuacion("esal")
