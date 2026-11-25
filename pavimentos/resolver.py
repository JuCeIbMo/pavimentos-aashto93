"""Resolución completa de un proyecto flexible: módulos 1 → 2 → 4 → 6 encadenados.

`resolver(proyecto)` es una función pura: recibe un `ProyectoFlexible` y devuelve un
diccionario con todos los resultados intermedios y finales, la lista de **decisiones**
de diseño (qué se adoptó y por qué) y la lista de **avisos** (datos fuera de rango,
inconsistencias). La interfaz, el PDF, el Excel, los escenarios y la validación usan
esta misma salida.
"""

from __future__ import annotations

import math

from pavimentos.ambiental import DatosInvalidos as ErrorAmbiental
from pavimentos.ambiental import periodo_desempeno
from pavimentos.formato import g, num
from pavimentos.flexible import coef_a1, coef_a2, coef_a3, log_w18, r_etapa, sn_requerido, zr_de_r
from pavimentos.lef import DatosInvalidos as ErrorLEF
from pavimentos.lef import cargar_lef, lef_eje
from pavimentos.modelo import ProyectoFlexible
from pavimentos.resiliente import DatosInvalidos as ErrorMR
from pavimentos.resiliente import danio_relativo, mr_de_cbr
from pavimentos.trafico import factor_crecimiento
from pavimentos.unidades import cm_a_pulg, pulg_a_cm

_TABLAS = None

# Espesores mínimos AASHTO 93 (Parte II, sección 3.1.5) en pulgadas: (W18 máx, carpeta, base)
MINIMOS_AASHTO = [
    (50_000, 1.0, 4.0),
    (150_000, 2.0, 4.0),
    (500_000, 2.5, 4.0),
    (2_000_000, 3.0, 6.0),
    (7_000_000, 3.5, 6.0),
    (math.inf, 4.0, 6.0),
]


def tablas_lef() -> dict:
    global _TABLAS
    if _TABLAS is None:
        _TABLAS = cargar_lef()
    return _TABLAS


def e_base_de_cbr(cbr: float) -> float:
    """Módulo de la base granular (psi) a partir del CBR (Cabezas, 2006, §4.10.1)."""
    return 9380.0 * math.log(cbr) - 12960.0


def e_subbase_de_cbr(cbr: float) -> float:
    """Módulo de la subbase granular (psi) a partir del CBR (Cabezas, 2006, §4.10.1)."""
    return 4326.0 * math.log(cbr) + 241.0


def minimos_aashto(w18: float) -> tuple[float, float]:
    """(carpeta, base) mínimos en pulgadas según el tránsito."""
    for w_max, ca, base in MINIMOS_AASHTO:
        if w18 <= w_max:
            return ca, base
    return MINIMOS_AASHTO[-1][1:]


def redondear_arriba(x: float, paso: float) -> float:
    if paso <= 0:
        return x
    return math.ceil(x / paso - 1e-9) * paso


class _Registro:
    def __init__(self):
        self.avisos: list[dict] = []
        self.decisiones: list[dict] = []

    def aviso(self, modulo: str, texto: str, nivel: str = "warn"):
        self.avisos.append({"modulo": modulo, "nivel": nivel, "texto": texto})

    def decision(self, modulo: str, texto: str):
        self.decisiones.append({"modulo": modulo, "texto": texto})


# ---------------------------------------------------------------------------- #
#  Módulo 1 — Tránsito                                                          #
# ---------------------------------------------------------------------------- #
def _resolver_transito(p: ProyectoFlexible, reg: _Registro) -> dict | None:
    tr = p.transito
    if not tr.vehiculos:
        return None
    if not (0 < tr.fd <= 1) or not (0 < tr.fc <= 1):
        reg.aviso("transito", "Fd y Fc deben estar entre 0 y 1.", "error")
        return None
    if tr.fd not in (0.5, 1.0) and not (0.3 <= tr.fd <= 0.7):
        reg.aviso("transito", f"Fd = {g(tr.fd)} es inusual: AASHTO recomienda 0,3–0,7 (normalmente 0,5).")
    if tr.unidad_carga not in ("t", "kip"):
        reg.aviso("transito", f"Unidad de carga desconocida: {tr.unidad_carga}.", "error")
        return None
    if tr.unidad_carga == "t" and not tr.kip_por_t > 0:
        reg.aviso("transito", "La conversión t → kip debe ser positiva.", "error")
        return None
    tablas = tablas_lef()
    filas = []
    for v in tr.vehiculos:
        detalle = []
        if v.factor_camion is not None:
            fcam = float(v.factor_camion)
            origen = "dato"
        else:
            fcam = 0.0
            origen = "ejes"
            for tipo, carga in v.ejes:
                carga = float(carga)
                kip = carga if tr.unidad_carga == "kip" else carga * tr.kip_por_t
                if carga <= 0:
                    reg.aviso("transito", f"{v.nombre}: falta la carga de un eje {({'tandem': 'tándem', 'tridem': 'trídem'}).get(tipo, tipo)}.", "error")
                    lef = 0.0
                else:
                    try:
                        lef = lef_eje(tablas, tipo, tr.pt, kip, tr.sn_lef)
                    except ErrorLEF as e:
                        reg.aviso("transito", f"{v.nombre}: {e}", "error")
                        lef = 0.0
                detalle.append({"tipo": tipo, "carga": carga, "unidad": tr.unidad_carga,
                               "carga_kip": kip, "lef": lef})
                fcam += lef
        gc = factor_crecimiento(v.r, tr.n)
        esal1 = v.tpda * fcam * 365.0 * tr.fd * tr.fc
        filas.append({
            "nombre": v.nombre, "tpda": v.tpda, "r": v.r, "pesado": v.pesado,
            "factor_camion": fcam, "origen_fc": origen, "ejes": detalle,
            "g": gc, "esal1": esal1, "w": esal1 * gc,
            "w_bruto": v.tpda * fcam * 365.0 * gc,  # ambos sentidos, todos los carriles
        })
    if any(f["ejes"] for f in filas):
        if tr.unidad_carga == "kip":
            reg.decision("transito", f"Cargas por eje en kip; LEF leídos de las tablas AASHTO (pt = {g(tr.pt)}, "
                                     f"SN supuesto = {g(tr.sn_lef)}) con interpolación.")
        else:
            exacta = abs(tr.kip_por_t - 2.20462) < 1e-3
            modo = "exacta" if exacta else ("simplificada de cátedra" if tr.kip_por_t == 2 else "personalizada")
            fac = num(tr.kip_por_t, 4) if exacta else g(tr.kip_por_t)
            reg.decision("transito", f"Cargas por eje en toneladas, convertidas a kip con 1 t = {fac} kip "
                                     f"(conversión {modo}); LEF leídos de las tablas AASHTO (pt = {g(tr.pt)}, "
                                     f"SN supuesto = {g(tr.sn_lef)}) con interpolación.")
    tpda = sum(f["tpda"] for f in filas)
    tpda_p = sum(f["tpda"] for f in filas if f["pesado"])
    total_w = sum(f["w"] for f in filas)
    if total_w <= 0:
        reg.aviso("transito", "El tránsito acumulado es cero: revisá TPDA y ejes.", "error")
        return None
    if total_w < 50_000:
        reg.aviso("transito", "W18 < 50.000 ESAL: el método AASHTO 93 está pensado para "
                  "tránsitos mayores (guía, Parte II, cap. 1).")

    def w_t(t: float) -> float:
        return sum(f["esal1"] * factor_crecimiento(f["r"], t) for f in filas)

    return {
        "filas": filas, "tpda_total": tpda, "tpda_pesados": tpda_p,
        "pesados_pct": 100.0 * tpda_p / tpda if tpda else 0.0,
        "esal1_total": sum(f["esal1"] for f in filas),
        "w18": total_w, "n": tr.n, "fd": tr.fd, "fc": tr.fc,
        "pt_lef": tr.pt, "sn_lef": tr.sn_lef, "unidad_carga": tr.unidad_carga,
        "kip_por_t": tr.kip_por_t, "_w_t": w_t,
    }


# ---------------------------------------------------------------------------- #
#  Módulo 2 — Subrasante                                                        #
# ---------------------------------------------------------------------------- #
def _resolver_subrasante(p: ProyectoFlexible, reg: _Registro) -> dict | None:
    per = p.subrasante.periodos
    if not per:
        return None
    filas = []
    for x in per:
        try:
            if x.mr is not None:
                mr, origen = float(x.mr), "dato"
            elif x.cbr is not None:
                mr, origen = mr_de_cbr(float(x.cbr)), ("1500·CBR" if x.cbr < 7.2 else "3000·CBR^0,65")
            else:
                reg.aviso("subrasante", f"{x.nombre}: falta CBR o M_R.", "error")
                return None
        except ErrorMR as e:
            reg.aviso("subrasante", f"{x.nombre}: {e}", "error")
            return None
        if mr <= 0:
            reg.aviso("subrasante", f"{x.nombre}: M_R debe ser positivo.", "error")
            return None
        uf = danio_relativo(mr)
        filas.append({"nombre": x.nombre, "meses": float(x.meses), "cbr": x.cbr, "mr": mr,
                      "origen": origen, "uf": uf, "uf_meses": uf * float(x.meses)})
    meses = sum(f["meses"] for f in filas)
    if abs(meses - 12.0) > 1e-6:
        reg.aviso("subrasante", f"Los períodos deben cubrir 12 meses (suman {g(meses)}).", "error")
        return None
    suma = sum(f["uf_meses"] for f in filas)
    uf_bar = suma / 12.0
    mr_ef = (uf_bar / 1.18e8) ** (-1 / 2.32)
    mrs = [f["mr"] for f in filas]
    if max(mrs) / min(mrs) > 5:
        reg.aviso("subrasante", "La variación estacional de M_R es muy grande (máx/mín > 5): "
                  "verificá los datos (puede ser correcto si hay congelamiento).", "info")
    reg.decision("subrasante",
                 f"Se adopta M_R efectivo = {num(mr_ef, 0)} psi, el valor que produce el mismo daño "
                 f"anual que la variación estacional (ū_f = {num(uf_bar, 4)}). Es menor que el promedio "
                 f"aritmético ({num(sum(f['mr'] * f['meses'] for f in filas) / 12, 0)} psi) porque los "
                 f"meses débiles dañan mucho más.")
    return {"filas": filas, "suma_uf": suma, "uf_bar": uf_bar, "mr_efectivo": mr_ef,
            "mr_promedio": sum(f["mr"] * f["meses"] for f in filas) / 12.0}


# ---------------------------------------------------------------------------- #
#  Módulo 4 — Parámetros de diseño y materiales                                 #
# ---------------------------------------------------------------------------- #
def _materiales(p: ProyectoFlexible, reg: _Registro) -> dict | None:
    d = p.diseno
    out = {}
    # Carpeta
    if d.carpeta.e_psi is None and d.carpeta.a is None:
        reg.aviso("diseno", "Falta E o a1 de la carpeta asfáltica.", "error")
        return None
    e1 = d.carpeta.e_psi
    if d.carpeta.a is not None:
        a1, o1 = d.carpeta.a, "dato"
    else:
        a1, o1 = coef_a1(e1), "0,17·ln(E_CA) − 1,7754"
        if not (100_000 <= e1 <= 600_000):
            reg.aviso("diseno", f"E_CA = {num(e1, 0)} psi fuera del rango usual de la correlación "
                      "(≈ 100.000–450.000 psi).")
    out["carpeta"] = {"e": e1, "a": a1, "origen_a": o1, "origen_e": "dato"}

    for nombre, capa, fe, fa, txt_e, txt_a in (
        ("base", d.base, e_base_de_cbr, coef_a2, "9380·ln(CBR) − 12960", "0,249·log(E_B) − 0,977"),
        ("subbase", d.subbase, e_subbase_de_cbr, coef_a3, "4326·ln(CBR) + 241", "0,227·log(E_SB) − 0,839"),
    ):
        if capa.e_psi is not None:
            e, oe = float(capa.e_psi), "dato"
        elif capa.cbr is not None and capa.cbr > 0:
            e, oe = fe(float(capa.cbr)), txt_e
        else:
            if capa.a is None:
                reg.aviso("diseno", f"Falta E, CBR o a de la {nombre}.", "error")
                return None
            e, oe = None, "—"
        if capa.a is not None:
            a, oa = float(capa.a), "dato"
        else:
            a, oa = fa(e), txt_a
        if e is not None and e <= 0:
            reg.aviso("diseno", f"El módulo de la {nombre} resultó ≤ 0: revisá el CBR.", "error")
            return None
        if a <= 0:
            reg.aviso("diseno", f"El coeficiente a de la {nombre} resultó ≤ 0.", "error")
            return None
        if not (0.4 <= capa.m <= 1.4):
            reg.aviso("diseno", f"m de la {nombre} = {g(capa.m)} fuera del rango AASHTO (0,40–1,40).")
        out[nombre] = {"e": e, "a": a, "m": capa.m, "origen_a": oa, "origen_e": oe, "cbr": capa.cbr}
    if out["base"]["e"] is None or out["subbase"]["e"] is None:
        reg.aviso("diseno", "Para el diseño por capas hace falta el módulo E de base y subbase "
                  "(SN1 y SN2 se calculan con ellos).", "error")
        return None
    if out["base"]["e"] < out["subbase"]["e"]:
        reg.aviso("diseno", "E de la base es menor que E de la subbase: la estructura queda invertida.")
    return out


def _espesores(w, zr, so, dpsi, mr, mat, d, reg: _Registro) -> dict:
    """Diseño por capas (guía AASHTO 93, Parte II, fig. 3.2)."""
    pulg = d.unidad == "pulg"

    def a_unidad(x_pulg):
        return x_pulg if pulg else pulg_a_cm(x_pulg)

    def a_pulg(x_u):
        return x_u if pulg else cm_a_pulg(x_u)

    if d.minimos == "aashto":
        mca, mb = minimos_aashto(w)
        mins = (redondear_arriba(a_unidad(mca), d.paso_espesor),
                redondear_arriba(a_unidad(mb), d.paso_espesor), 0.0)
        origen_min = (f"tabla AASHTO para W18 = {num(w, 0)}: carpeta {g(mca)}\", base {g(mb)}\"")
    elif d.minimos == "personalizado":
        mins = (d.min_carpeta, d.min_base, d.min_subbase)
        origen_min = "mínimos constructivos definidos por el proyectista"
    else:
        mins = (0.0, 0.0, 0.0)
        origen_min = "sin mínimos"

    e_b, e_sb = mat["base"]["e"], mat["subbase"]["e"]
    a1, a2, a3 = mat["carpeta"]["a"], mat["base"]["a"], mat["subbase"]["a"]
    m2, m3 = mat["base"]["m"], mat["subbase"]["m"]
    sn1 = sn_requerido(w, zr, so, dpsi, e_b)
    sn2 = sn_requerido(w, zr, so, dpsi, e_sb)
    sn3 = sn_requerido(w, zr, so, dpsi, mr)
    u = "pulg" if pulg else "cm"

    # Capa 1
    d1_calc = a_unidad(sn1 / a1)
    d1 = max(redondear_arriba(d1_calc, d.paso_espesor), mins[0])
    sn1s = a1 * a_pulg(d1)
    # Capa 2
    falta2 = sn2 - sn1s
    d2_calc = a_unidad(falta2 / (a2 * m2)) if falta2 > 0 else 0.0
    d2 = max(redondear_arriba(d2_calc, d.paso_espesor), mins[1])
    sn2s = a2 * m2 * a_pulg(d2)
    # Capa 3
    falta3 = sn3 - sn1s - sn2s
    d3_calc = a_unidad(falta3 / (a3 * m3)) if falta3 > 0 else 0.0
    d3 = max(redondear_arriba(d3_calc, d.paso_espesor), mins[2])
    sn3s = a3 * m3 * a_pulg(d3)
    total = sn1s + sn2s + sn3s

    gobierna = []
    if d1 > redondear_arriba(d1_calc, d.paso_espesor):
        gobierna.append("carpeta")
    if d2 > redondear_arriba(d2_calc, d.paso_espesor):
        gobierna.append("base")
    reg.decision("diseno", f"Espesores redondeados hacia arriba a {g(d.paso_espesor)} {u}; mínimos: {origen_min}.")
    if gobierna:
        reg.decision("diseno", f"En {' y '.join(gobierna)} gobierna el espesor mínimo, no el cálculo.")
    if falta2 <= 0:
        reg.decision("diseno", "La carpeta ya aporta el SN2 requerido: la base se coloca por el mínimo constructivo.")
    if falta3 <= 0:
        reg.decision("diseno", "Carpeta + base ya cubren SN3: la subbase no es necesaria estructuralmente.")

    capas = [
        {"capa": "Carpeta asfáltica", "a": a1, "m": None, "sn_req": sn1, "d_calc": d1_calc, "d": d1,
         "d_pulg": a_pulg(d1), "d_cm": pulg_a_cm(a_pulg(d1)), "sn_aporte": sn1s, "minimo": mins[0]},
        {"capa": "Base granular", "a": a2, "m": m2, "sn_req": sn2, "d_calc": d2_calc, "d": d2,
         "d_pulg": a_pulg(d2), "d_cm": pulg_a_cm(a_pulg(d2)), "sn_aporte": sn2s, "minimo": mins[1]},
        {"capa": "Subbase granular", "a": a3, "m": m3, "sn_req": sn3, "d_calc": d3_calc, "d": d3,
         "d_pulg": a_pulg(d3), "d_cm": pulg_a_cm(a_pulg(d3)), "sn_aporte": sn3s, "minimo": mins[2]},
    ]
    verif = [
        {"criterio": "SN1* ≥ SN1 (protege la base)", "izq": sn1s, "der": sn1, "cumple": sn1s >= sn1 - 1e-9},
        {"criterio": "SN1* + SN2* ≥ SN2 (protege la subbase)", "izq": sn1s + sn2s, "der": sn2,
         "cumple": sn1s + sn2s >= sn2 - 1e-9},
        {"criterio": "SN total ≥ SN3 (protege la subrasante)", "izq": total, "der": sn3,
         "cumple": total >= sn3 - 1e-9},
    ]
    return {"unidad": u, "capas": capas, "sn1": sn1, "sn2": sn2, "sn3": sn3,
            "sn_total": total, "verificaciones": verif, "cumple": all(v["cumple"] for v in verif),
            "espesor_total": d1 + d2 + d3, "minimos": mins, "origen_minimos": origen_min}


# ---------------------------------------------------------------------------- #
#  Resolución completa                                                          #
# ---------------------------------------------------------------------------- #
def resolver(p: ProyectoFlexible) -> dict:
    reg = _Registro()
    d = p.diseno
    res: dict = {"proyecto": p.nombre, "transito": None, "subrasante": None,
                 "diseno": None, "clima": None, "capas": None}

    # 1) Tránsito
    tr = _resolver_transito(p, reg)
    res["transito"] = tr

    # 2) Subrasante
    sub = _resolver_subrasante(p, reg)
    res["subrasante"] = sub

    # 4) Parámetros de diseño
    if d.fuente_w18 == "dato":
        w18, fuente_w = d.w18_dato, "un dato del proyecto"
    else:
        w18, fuente_w = (tr["w18"] if tr else None), "el módulo 1 (tránsito)"
    if not w18 or w18 <= 0:
        reg.aviso("diseno", "Falta el tránsito de diseño W18: calculalo en el módulo 1 o ingresalo como dato.", "error")
        return _cerrar(res, reg)
    if d.fuente_mr == "dato":
        mr, fuente_mr = d.mr_dato, "un dato del proyecto"
    else:
        mr, fuente_mr = (sub["mr_efectivo"] if sub else None), "el módulo 2 (subrasante)"
    if not mr or mr <= 0:
        reg.aviso("diseno", "Falta el M_R efectivo: calculalo en el módulo 2 o ingresalo como dato.", "error")
        return _cerrar(res, reg)

    if not (50 <= d.r_pct < 100):
        reg.aviso("diseno", "La confiabilidad R debe estar entre 50 % y 99,99 %.", "error")
        return _cerrar(res, reg)
    r_et = r_etapa(d.r_pct, d.etapas) if d.etapas > 1 else d.r_pct
    zr = zr_de_r(r_et)
    dpsi = d.p0 - d.pt
    if dpsi <= 0:
        reg.aviso("diseno", "ΔPSI = p0 − pt debe ser positivo.", "error")
        return _cerrar(res, reg)
    if not (0.30 <= d.so <= 0.50):
        reg.aviso("diseno", f"So = {g(d.so)} fuera del rango AASHTO para flexibles (0,40–0,50).")
    elif not (0.40 <= d.so <= 0.50):
        reg.aviso("diseno", f"So = {g(d.so)}: AASHTO recomienda 0,40–0,50 para flexibles.", "info")
    if d.p0 > 4.6 or d.pt < 1.5:
        reg.aviso("diseno", "p0 > 4,6 o pt < 1,5 están fuera de los valores habituales.")
    usa_ejes = bool(tr) and any(f["origen_fc"] == "ejes" for f in tr["filas"])
    if usa_ejes and abs(tr["pt_lef"] - d.pt) > 1e-9:
        reg.aviso("transito", f"Los LEF se calcularon con pt = {g(tr['pt_lef'])} y el diseño usa pt = {g(d.pt)}: "
                  "conviene usar el mismo valor.", "info")

    if d.etapas > 1:
        reg.decision("diseno", f"Construcción por {d.etapas} etapas: la confiabilidad de cada etapa es "
                     f"R^(1/{d.etapas}) = {num(r_et, 1)} % para que el conjunto cumpla R = {g(d.r_pct)} %.")
    reg.decision("diseno", f"W18 de diseño tomado de {fuente_w}; M_R de {fuente_mr}.")

    so = d.so
    sn_req = sn_requerido(w18, zr, so, dpsi, mr)
    sn_adop = redondear_arriba(sn_req, d.paso_sn) if d.paso_sn > 0 else sn_req
    if d.paso_sn > 0:
        reg.decision("diseno", f"SN requerido = {num(sn_req, 3)}; se adopta SN = {num(sn_adop, 2)} "
                     f"(redondeo hacia arriba a {g(d.paso_sn)}).")
    if usa_ejes and abs(tr["sn_lef"] - sn_adop) > 0.5:
        reg.aviso("transito", f"Los LEF se calcularon con SN supuesto = {g(tr['sn_lef'])}, pero el SN "
                  f"resultante es {num(sn_adop, 1)}. Conviene repetir el módulo 1 con un SN más cercano.")

    mat = _materiales(p, reg)
    if mat is None:
        return _cerrar(res, reg)

    res["diseno"] = {
        "w18": w18, "fuente_w18": fuente_w, "log_w18": math.log10(w18),
        "mr": mr, "fuente_mr": fuente_mr, "r_pct": d.r_pct, "etapas": d.etapas,
        "r_etapa": r_et, "zr": zr, "so": so, "p0": d.p0, "pt": d.pt, "dpsi": dpsi,
        "sn_requerido": sn_req, "sn_adoptado": sn_adop, "materiales": mat,
        # comprobación: con el SN adoptado, la ecuación admite al menos W18
        "log_w_admisible": log_w18(sn_adop, zr, so, dpsi, mr),
    }

    # 6) Clima
    w_dis, dpsi_dis = w18, dpsi
    if p.clima.activo:
        c = p.clima
        if tr is None:
            reg.aviso("clima", "El ajuste climático necesita el tránsito del módulo 1 "
                      "(para saber en cuántos años se acumula cada W).", "error")
        else:
            helada = None
            if c.helada is not None:
                helada = {"pf": c.helada.pf, "dpsi_max": c.helada.dpsi_max, "phi": c.helada.phi}
            try:
                amb = periodo_desempeno(sn_adop, mr, dpsi, zr, so,
                                        c.vr if c.hinchamiento else 0.0,
                                        c.ps if c.hinchamiento else 0.0,
                                        c.theta, tr["n"], tr["_w_t"], helada)
                res["clima"] = {**amb, "t_objetivo": tr["n"]}
                w_dis, dpsi_dis = amb["w_adm"], amb["dpsi_tr"]
                if amb["periodo"] < tr["n"] - 0.05:
                    reg.decision("clima",
                                 f"Por efectos ambientales el pavimento rinde {num(amb['periodo'], 1)} años en lugar de "
                                 f"{g(tr['n'])}: hay que prever una rehabilitación (recapado) a esa edad o "
                                 f"aumentar el SN.")
                reg.decision("clima",
                             f"Los espesores se diseñan con el tránsito admisible W = {num(amb['w_adm'], 0)} y la "
                             f"pérdida de serviciabilidad remanente para tránsito ΔPSI_TR = {num(amb['dpsi_tr'], 3)}.")
            except ErrorAmbiental as e:
                reg.aviso("clima", str(e), "error")

    res["capas"] = _espesores(w_dis, zr, so, dpsi_dis, mr, mat, d, reg)
    res["capas"]["w_diseno"] = w_dis
    res["capas"]["dpsi_diseno"] = dpsi_dis
    if not res["capas"]["cumple"]:
        reg.aviso("diseno", "La estructura NO cumple alguna verificación de SN.", "error")
    return _cerrar(res, reg)


def _cerrar(res: dict, reg: _Registro) -> dict:
    res["avisos"] = reg.avisos
    res["decisiones"] = reg.decisiones
    res["ok"] = res.get("capas") is not None and not any(a["nivel"] == "error" for a in reg.avisos)
    return res


def limpiar(res: dict) -> dict:
    """Copia del resultado sin callables (para serializar)."""
    out = dict(res)
    if out.get("transito"):
        out["transito"] = {k: v for k, v in out["transito"].items() if not k.startswith("_")}
    return out
