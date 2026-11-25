"""Libro Excel con fórmulas vivas.

Cada hoja reproduce un módulo con fórmulas de Excel (no valores pegados), de modo que
quien revise el libro pueda cambiar un dato y ver cómo se recalcula todo. El número
estructural se resuelve en la hoja «SN (bisección)» con 50 iteraciones de bisección
escritas como fórmulas, así que también es vivo.

Lo único que va como valor es lo que no tiene fórmula cerrada: los LEF tabulados
(Apéndice D) y la iteración del período de desempeño por clima (que se muestra
resuelta, con sus iteraciones).
"""

from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from pavimentos.modelo import ProyectoFlexible
from pavimentos.referencias import REFERENCIAS
from pavimentos.resolver import resolver

AMBAR = "C98A00"
OSCURO = "1F2937"
F_TIT = Font(bold=True, size=14, color=OSCURO)
F_SUB = Font(italic=True, size=9, color="6B7280")
F_ENC = Font(bold=True, color="FFFFFF")
F_NEG = Font(bold=True)
R_ENC = PatternFill("solid", fgColor=OSCURO)
R_DATO = PatternFill("solid", fgColor="FFF7E0")      # celdas editables
R_RES = PatternFill("solid", fgColor="E8F5E9")       # resultados clave
BORDE = Border(bottom=Side(style="thin", color="D1D5DB"))

N0, N2, N3, N4 = "#,##0", "0.00", "0.000", "0.0000"


class _Hoja:
    def __init__(self, ws, titulo: str, subtitulo: str = ""):
        self.ws = ws
        ws["A1"] = titulo
        ws["A1"].font = F_TIT
        if subtitulo:
            ws["A2"] = subtitulo
            ws["A2"].font = F_SUB
        self.fila = 4

    def seccion(self, texto: str):
        self.fila += 1
        c = self.ws.cell(self.fila, 1, texto)
        c.font = Font(bold=True, size=11, color=AMBAR)
        self.fila += 1

    def par(self, etiqueta: str, valor, fmt: str | None = None, dato: bool = False,
            resultado: bool = False, nota: str = "") -> str:
        """Escribe «etiqueta | valor | nota» y devuelve la dirección absoluta del valor."""
        ws = self.ws
        ws.cell(self.fila, 1, etiqueta)
        c = ws.cell(self.fila, 2, valor)
        if fmt:
            c.number_format = fmt
        if dato:
            c.fill = R_DATO
        if resultado:
            c.fill = R_RES
            c.font = F_NEG
        if nota:
            ws.cell(self.fila, 3, nota).font = F_SUB
        ref = f"${get_column_letter(2)}${self.fila}"
        self.fila += 1
        return ref

    def encabezado(self, columnas: list[str]):
        for j, t in enumerate(columnas, start=1):
            c = self.ws.cell(self.fila, j, t)
            c.font, c.fill = F_ENC, R_ENC
            c.alignment = Alignment(horizontal="center", wrap_text=True)
        self.fila += 1

    def anchos(self, *anchos):
        for j, a in enumerate(anchos, start=1):
            self.ws.column_dimensions[get_column_letter(j)].width = a


def _q(nombre: str) -> str:
    return f"'{nombre}'"


def generar_excel(p: ProyectoFlexible, res: dict | None = None) -> bytes:
    res = res or resolver(p)
    wb = Workbook()
    d = p.diseno
    refs: dict[str, str] = {}

    # ------------------------------------------------------------------ Tránsito
    tr = res.get("transito")
    if tr:
        ws = wb.active
        ws.title = "Transito"
        h = _Hoja(ws, "Módulo 1 · Tránsito (ESAL / W18)",
                  "Celdas amarillas = datos editables. G = ((1+r)^n − 1)/r ; ESAL₁ = TPDA·FC·365·Fd·Fc ; W = ESAL₁·G")
        h.anchos(30, 14, 12, 12, 12, 16, 18)
        n = h.par("Período de diseño n (años)", tr["n"], "0", dato=True)
        fd = h.par("Distribución direccional Fd", tr["fd"], N2, dato=True)
        fc = h.par("Distribución por carril Fc", tr["fc"], N2, dato=True)
        h.fila += 1
        h.encabezado(["Vehículo", "TPDA", "r", "FC (Σ LEF)", "G", "ESAL año 1", "W (n años)"])
        f0 = h.fila
        for f in tr["filas"]:
            i = h.fila
            ws.cell(i, 1, f["nombre"])
            ws.cell(i, 2, f["tpda"]).fill = R_DATO
            c = ws.cell(i, 3, f["r"])
            c.fill, c.number_format = R_DATO, "0.0%"
            c = ws.cell(i, 4, round(f["factor_camion"], 6))
            c.fill, c.number_format = R_DATO, N4
            ws.cell(i, 5, f"=IF(C{i}=0,{n},((1+C{i})^{n}-1)/C{i})").number_format = N3
            ws.cell(i, 6, f"=B{i}*D{i}*365*{fd}*{fc}").number_format = N0
            ws.cell(i, 7, f"=F{i}*E{i}").number_format = N0
            h.fila += 1
        f1 = h.fila - 1
        ws.cell(h.fila, 1, "TOTAL").font = F_NEG
        ws.cell(h.fila, 2, f"=SUM(B{f0}:B{f1})").number_format = N0
        ws.cell(h.fila, 6, f"=SUM(F{f0}:F{f1})").number_format = N0
        c = ws.cell(h.fila, 7, f"=SUM(G{f0}:G{f1})")
        c.number_format, c.fill, c.font = N0, R_RES, F_NEG
        refs["w18"] = f"Transito!$G${h.fila}"
        h.fila += 2
        ws.cell(h.fila, 1, "El FC de cada vehículo es la suma de los LEF de sus ejes (hoja «LEF», tablas "
                           "AASHTO D.1–D.9) o un dato de pesaje.").font = F_SUB

        if any(f["ejes"] for f in tr["filas"]):
            wl = wb.create_sheet("LEF")
            hl = _Hoja(wl, "Factores de equivalencia de carga por eje",
                       f"AASHTO 93, Apéndice D · pt = {tr['pt_lef']:g} · SN supuesto = {tr['sn_lef']:g} · interpolación bilineal")
            hl.anchos(30, 12, 12, 12, 12)
            en_t = tr["unidad_carga"] == "t"
            hl.encabezado(["Vehículo", "Tipo de eje", f"Carga ({tr['unidad_carga']})", "Carga usada (kip)", "LEF"])
            if en_t:
                wl.cell(2, 7, "kip por tonelada")
                wl.cell(2, 8, tr["kip_por_t"]).fill = R_DATO
            for f in tr["filas"]:
                for e in f["ejes"]:
                    i = hl.fila
                    wl.cell(i, 1, f["nombre"])
                    wl.cell(i, 2, e["tipo"])
                    wl.cell(i, 3, e["carga"])
                    wl.cell(i, 4, f"=C{i}*$H$2" if en_t else f"=C{i}").number_format = "0.00"
                    wl.cell(i, 5, round(e["lef"], 6)).number_format = N4
                    hl.fila += 1
    else:
        wb.active.title = "Datos"

    # ------------------------------------------------------------------ Subrasante
    sub = res.get("subrasante")
    if sub:
        ws = wb.create_sheet("Subrasante")
        h = _Hoja(ws, "Módulo 2 · Módulo resiliente efectivo",
                  "M_R = 1500·CBR (CBR<7,2) ó 3000·CBR^0,65 ; u_f = 1,18e8·M_R^−2,32 ; M_R,ef = (ū_f/1,18e8)^(−1/2,32)")
        h.anchos(34, 10, 10, 14, 12, 14)
        h.encabezado(["Período", "Meses", "CBR (%)", "M_R (psi)", "u_f", "u_f · meses"])
        f0 = h.fila
        for x, f in zip(p.subrasante.periodos, sub["filas"]):
            i = h.fila
            ws.cell(i, 1, f["nombre"])
            ws.cell(i, 2, f["meses"]).fill = R_DATO
            if x.mr is not None:
                ws.cell(i, 3, "—")
                c = ws.cell(i, 4, f["mr"])
                c.fill = R_DATO
            else:
                ws.cell(i, 3, f["cbr"]).fill = R_DATO
                c = ws.cell(i, 4, f"=IF(C{i}<7.2,1500*C{i},3000*C{i}^0.65)")
            c.number_format = N0
            ws.cell(i, 5, f"=1.18E8*D{i}^-2.32").number_format = N4
            ws.cell(i, 6, f"=E{i}*B{i}").number_format = N4
            h.fila += 1
        f1 = h.fila - 1
        ws.cell(h.fila, 1, "SUMA").font = F_NEG
        ws.cell(h.fila, 2, f"=SUM(B{f0}:B{f1})")
        ws.cell(h.fila, 6, f"=SUM(F{f0}:F{f1})").number_format = N4
        suma = f"$F${h.fila}"
        h.fila += 2
        uf = h.par("Daño relativo promedio ū_f", f"={suma}/12", N4)
        refs["mr"] = "Subrasante!" + h.par("M_R efectivo (psi)", f"=({uf}/1.18E8)^(-1/2.32)", N0, resultado=True)

    # ------------------------------------------------------------------ Diseño
    di, ca = res.get("diseno"), res.get("capas")
    if di and ca:
        ws = wb.create_sheet("Diseno")
        h = _Hoja(ws, "Módulo 4 · Diseño estructural (AASHTO 93)",
                  "log W18 = ZR·So + 9,36·log(SN+1) − 0,20 + log(ΔPSI/2,7)/(0,40 + 1094/(SN+1)^5,19) + 2,32·log MR − 8,07")
        h.anchos(44, 16, 60)
        h.seccion("Parámetros")
        if d.fuente_w18 == "calculado" and "w18" in refs:
            w = h.par("W18 de diseño (ESAL)", f"={refs['w18']}", N0, nota="vinculado a la hoja Transito")
        else:
            w = h.par("W18 de diseño (ESAL)", di["w18"], N0, dato=True)
        if d.fuente_mr == "calculado" and "mr" in refs:
            mr = h.par("M_R efectivo (psi)", f"={refs['mr']}", N0, nota="vinculado a la hoja Subrasante")
        else:
            mr = h.par("M_R efectivo (psi)", di["mr"], N0, dato=True)
        r = h.par("Confiabilidad R (%)", di["r_pct"], N2, dato=True)
        et = h.par("Número de etapas", di["etapas"], "0", dato=True)
        ret = h.par("R por etapa (%)", f"=100*({r}/100)^(1/{et})", N2)
        zr = h.par("Z_R", f"=NORMSINV(1-{ret}/100)", N3)
        so = h.par("Desviación estándar So", di["so"], N2, dato=True)
        p0 = h.par("Serviciabilidad inicial p0", di["p0"], "0.0", dato=True)
        pt = h.par("Serviciabilidad terminal pt", di["pt"], "0.0", dato=True)
        dpsi = h.par("ΔPSI = p0 − pt", f"={p0}-{pt}", N2)

        h.seccion("Materiales")
        mat = di["materiales"]
        eca = h.par("E carpeta asfáltica (psi)", mat["carpeta"]["e"], N0, dato=True)
        a1 = (h.par("a1 (dato)", mat["carpeta"]["a"], N4, dato=True) if d.carpeta.a is not None
              else h.par("a1 = 0,17·ln(E_CA) − 1,7754", f"=0.17*LN({eca})-1.7754", N4))
        if d.base.e_psi is None and d.base.cbr is not None:
            cb = h.par("CBR base (%)", d.base.cbr, "0.0", dato=True)
            eb = h.par("E base = 9380·ln(CBR) − 12960 (psi)", f"=9380*LN({cb})-12960", N0)
        else:
            eb = h.par("E base (psi)", mat["base"]["e"], N0, dato=True)
        a2 = (h.par("a2 (dato)", mat["base"]["a"], N4, dato=True) if d.base.a is not None
              else h.par("a2 = 0,249·log(E_B) − 0,977", f"=0.249*LOG10({eb})-0.977", N4))
        if d.subbase.e_psi is None and d.subbase.cbr is not None:
            csb = h.par("CBR subbase (%)", d.subbase.cbr, "0.0", dato=True)
            esb = h.par("E subbase = 4326·ln(CBR) + 241 (psi)", f"=4326*LN({csb})+241", N0)
        else:
            esb = h.par("E subbase (psi)", mat["subbase"]["e"], N0, dato=True)
        a3 = (h.par("a3 (dato)", mat["subbase"]["a"], N4, dato=True) if d.subbase.a is not None
              else h.par("a3 = 0,227·log(E_SB) − 0,839", f"=0.227*LOG10({esb})-0.839", N4))
        m2 = h.par("m2 (drenaje base)", d.base.m, N2, dato=True)
        m3 = h.par("m3 (drenaje subbase)", d.subbase.m, N2, dato=True)

        h.seccion("Tránsito y ΔPSI usados para las capas")
        if res.get("clima"):
            wc = h.par("W para capas (admisible por clima)", ca["w_diseno"], N0,
                       nota="resultado de la iteración climática (hoja Clima)")
            dpc = h.par("ΔPSI para capas (ΔPSI_TR)", ca["dpsi_diseno"], N3, nota="ΔPSI − ΔPSI_SW − ΔPSI_FH")
        else:
            wc = h.par("W para capas", f"={w}", N0)
            dpc = h.par("ΔPSI para capas", f"={dpsi}", N3)

        # Hoja de bisección (SN vivos)
        wsb = wb.create_sheet("SN (biseccion)")
        hb = _Hoja(wsb, "Resolución del SN por bisección (50 iteraciones, todo en fórmulas)",
                   "Para cada caso: si F(SN medio) < log W se sube el límite inferior; si no, se baja el superior.")
        casos = [("SN requerido (W18, M_R)", w, dpsi, mr), ("SN1 (sobre base, E_B)", wc, dpc, eb),
                 ("SN2 (sobre subbase, E_SB)", wc, dpc, esb), ("SN3 (sobre subrasante, M_R)", wc, dpc, mr)]
        resultados_sn = []
        fila_ini = 6
        for k, (nombre, w_, dp_, m_) in enumerate(casos):
            col = 1 + k * 4
            L, H, M, F = (get_column_letter(col + j) for j in range(4))
            wsb.cell(4, col, nombre).font = Font(bold=True, color=AMBAR)
            for j, t in enumerate(["inferior", "superior", "SN medio", "F − log W"]):
                c = wsb.cell(5, col + j, t)
                c.font, c.fill = F_ENC, R_ENC
            for it in range(50):
                i = fila_ini + it
                if it == 0:
                    wsb[f"{L}{i}"] = 0.01
                    wsb[f"{H}{i}"] = 20
                else:
                    wsb[f"{L}{i}"] = f"=IF({F}{i - 1}<0,{M}{i - 1},{L}{i - 1})"
                    wsb[f"{H}{i}"] = f"=IF({F}{i - 1}<0,{H}{i - 1},{M}{i - 1})"
                wsb[f"{M}{i}"] = f"=({L}{i}+{H}{i})/2"
                sn = f"{M}{i}"
                wsb[f"{F}{i}"] = (f"=Diseno!{zr}*Diseno!{so}+9.36*LOG10({sn}+1)-0.2"
                                  f"+LOG10(Diseno!{dp_}/2.7)/(0.4+1094/({sn}+1)^5.19)"
                                  f"+2.32*LOG10(Diseno!{m_})-8.07-LOG10(Diseno!{w_})")
                wsb[f"{M}{i}"].number_format = N4
            resultados_sn.append(f"'SN (biseccion)'!${M}${fila_ini + 49}")
        for j in range(16):
            wsb.column_dimensions[get_column_letter(j + 1)].width = 11

        h.seccion("Número estructural")
        snr = h.par("SN requerido", f"={resultados_sn[0]}", N3, resultado=True)
        h.par("SN adoptado (redondeo hacia arriba)",
              f"=CEILING({snr}-1E-9,{d.paso_sn})" if d.paso_sn > 0 else f"={snr}", N2, resultado=True)
        h.par("Verificación: log W admisible con SN requerido",
              f"={zr}*{so}+9.36*LOG10({snr}+1)-0.2+LOG10({dpsi}/2.7)/(0.4+1094/({snr}+1)^5.19)+2.32*LOG10({mr})-8.07",
              N3, nota="debe coincidir con log W18 →")
        h.par("log W18", f"=LOG10({w})", N3)
        sn1 = h.par("SN1 (protección de la base)", f"={resultados_sn[1]}", N3)
        sn2 = h.par("SN2 (protección de la subbase)", f"={resultados_sn[2]}", N3)
        sn3 = h.par("SN3 (protección de la subrasante)", f"={resultados_sn[3]}", N3)

        h.seccion(f"Espesores (unidad: {ca['unidad']})")
        fac = h.par("Factor de unidad (pulg → unidad)", 1 if ca["unidad"] == "pulg" else 2.54, N2,
                    nota="1 = pulgadas ; 2,54 = centímetros")
        paso = h.par("Paso de redondeo", d.paso_espesor, N2, dato=True)
        mins = ca["minimos"]
        mn1 = h.par("Mínimo carpeta", mins[0], N2, dato=True, nota=ca["origen_minimos"])
        mn2 = h.par("Mínimo base", mins[1], N2, dato=True)
        mn3 = h.par("Mínimo subbase", mins[2], N2, dato=True)
        d1c = h.par("D1 calculado = SN1/a1", f"={sn1}/{a1}*{fac}", N2)
        d1 = h.par("D1 adoptado", f"=MAX(CEILING({d1c}-1E-9,{paso}),{mn1})", N2, resultado=True)
        s1 = h.par("SN1* = a1·D1", f"={a1}*{d1}/{fac}", N3)
        d2c = h.par("D2 calculado = (SN2 − SN1*)/(a2·m2)", f"=MAX(0,({sn2}-{s1})/({a2}*{m2}))*{fac}", N2)
        d2 = h.par("D2 adoptado", f"=MAX(CEILING({d2c}-1E-9,{paso}),{mn2})", N2, resultado=True)
        s2 = h.par("SN2* = a2·m2·D2", f"={a2}*{m2}*{d2}/{fac}", N3)
        d3c = h.par("D3 calculado = (SN3 − SN1* − SN2*)/(a3·m3)",
                    f"=MAX(0,({sn3}-{s1}-{s2})/({a3}*{m3}))*{fac}", N2)
        d3 = h.par("D3 adoptado", f"=MAX(CEILING({d3c}-1E-9,{paso}),{mn3})", N2, resultado=True)
        s3 = h.par("SN3* = a3·m3·D3", f"={a3}*{m3}*{d3}/{fac}", N3)
        tot = h.par("SN total aportado", f"={s1}+{s2}+{s3}", N3, resultado=True)

        h.seccion("Verificaciones")
        h.par("SN1* ≥ SN1", f'=IF({s1}>={sn1}-1E-9,"CUMPLE","NO CUMPLE")')
        h.par("SN1* + SN2* ≥ SN2", f'=IF({s1}+{s2}>={sn2}-1E-9,"CUMPLE","NO CUMPLE")')
        h.par("SN total ≥ SN3", f'=IF({tot}>={sn3}-1E-9,"CUMPLE","NO CUMPLE")', resultado=True)
        refs.update({"w": f"Diseno!{w}", "d1": f"Diseno!{d1}", "d2": f"Diseno!{d2}", "d3": f"Diseno!{d3}",
                     "sn": f"Diseno!{tot}", "snr": f"Diseno!{snr}"})

    # ------------------------------------------------------------------ Clima
    cl = res.get("clima")
    if cl:
        ws = wb.create_sheet("Clima")
        h = _Hoja(ws, "Módulo 6 · Período de desempeño por clima",
                  "ΔPSI_SW = 0,00335·VR·PS·(1 − e^(−θt)) ; ΔPSI_FH = 0,01·PF·ΔPSI_MAX·(1 − e^(−0,02·φ·t))")
        h.anchos(22, 14, 14, 14, 16, 14)
        h.par("VR (pulg)", p.clima.vr, N2)
        h.par("PS (%)", p.clima.ps, "0.0")
        h.par("θ", p.clima.theta, N3)
        h.fila += 1
        h.encabezado(["t supuesto", "ΔPSI_SW", "ΔPSI_FH", "ΔPSI_TR", "W admisible", "t calculado"])
        for it in cl["iteraciones"]:
            i = h.fila
            for j, k in enumerate(["t", "dpsi_sw", "dpsi_fh", "dpsi_tr", "w_adm", "t_calc"], start=1):
                c = ws.cell(i, j, it[k])
                c.number_format = N0 if k == "w_adm" else N3
            h.fila += 1
        h.fila += 1
        h.par("Período de desempeño (años)", cl["periodo"], N2, resultado=True)
        h.par("W admisible", cl["w_adm"], N0)

    # ------------------------------------------------------------------ Resumen (primera hoja)
    ws = wb.create_sheet("Resumen", 0)
    h = _Hoja(ws, p.nombre or "Proyecto", "Diseño de pavimento flexible — AASHTO 1993 · libro con fórmulas vivas")
    h.anchos(40, 22, 50)
    h.par("Autor", p.autor or "—")
    h.par("Ubicación", p.ubicacion or "—")
    if p.descripcion:
        h.par("Descripción", p.descripcion)
    if di and ca:
        h.seccion("Resultado")
        h.par("W18 de diseño", f"={refs['w']}", N0)
        h.par("SN requerido", f"={refs['snr']}", N3)
        u = ca["unidad"]
        h.par(f"Carpeta asfáltica ({u})", f"={refs['d1']}", N2, resultado=True)
        h.par(f"Base granular ({u})", f"={refs['d2']}", N2, resultado=True)
        h.par(f"Subbase granular ({u})", f"={refs['d3']}", N2, resultado=True)
        h.par("SN aportado", f"={refs['sn']}", N3)
    h.seccion("Cómo usar este libro")
    for t in ["Las celdas amarillas son datos: cambialas y todo se recalcula.",
              "Las verdes son resultados clave.",
              "El SN se resuelve en la hoja «SN (bisección)» con fórmulas (no hace falta Buscar objetivo).",
              "Los LEF y la iteración climática van como valores calculados por el programa."]:
        ws.cell(h.fila, 1, "• " + t)
        h.fila += 1
    h.seccion("Referencias")
    for _, t in REFERENCIAS.items():
        ws.cell(h.fila, 1, t.replace("*", ""))
        h.fila += 1

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
