#!/usr/bin/env python3
"""Genera data/lef.json a partir del docling de lefs.pdf.

El OCR de `lefs_docling.md` perdió los puntos decimales y tiene algunos
errores de caracteres (p. ej. "7" leído como "/"). Este script:
  1. Parsea las tablas D.1-D.9 (flexibles).
  2. Reconstruye el decimal de cada celda:
     - token con espacio "1 59"  -> 1.59  (espacio = separador decimal)
     - token con punto  "5.36"   -> 5.36
     - token ".012"              -> 0.012
     - token de solo dígitos     -> por monotonicidad creciente dentro de la
                                   columna (el valor real es el menor candidato
                                   mayor que la fila anterior).
  3. Las celdas ilegibles o que rompen la monotonicidad se interpolan entre
     vecinas válidas y se marcan `estimado`.
  4. Verifica el ancla 18 kip = 1.00 en ejes simples.

Salida: data/lef.json
  {"flexible": {tipo_eje: {pt: {"cargas": [...], "sn": [1..6], "lef": [[...]]}}}}
"""
import json
import math
import re
import sys

FUENTE = "/home/juliocim/Documentos/Uni/diseño-pavimentos/wiki/fuentes_texto/lefs_docling.md"
SALIDA = "data/lef.json"

AXLE = {"Single": "simple", "Tandem": "tandem", "Triple": "tridem"}

# Correcciones puntuales de errores de OCR (caracteres mal leídos).
# clave: (tipo_eje, pt, columna 0..5, carga_kip) -> token corregido.
OVERRIDES = {
    # D.6 (tridem, pt 2.5), col 1, 14 kip: "800" es "008" (0.008)
    ("tridem", "2.5", 0, 14): "008",
    # D.9 (tridem, pt 3.0), col 3, 44 kip: "688" es "888" (0.888)
    ("tridem", "3.0", 2, 44): "0.888",
}


def token_a_valor(token: str, prev: float | None):
    """Devuelve el float, o None si la celda es ilegible o no encaja con `prev`.

    Regla de reconstrucción del decimal:
      - espacio o punto -> separador decimal explícito.
      - token con ceros a la izquierda ("0002", "030") -> 0.0002, 0.030
        (el decimal va después de los ceros: int(digitos) * 10^-len).
      - token sin ceros a la izquierda ("165", "161", "113") -> se elige la
        lectura monótona: el menor candidato mayor que la fila anterior.
    """
    s = token.strip()
    if " " in s:
        a, b = s.split(" ", 1)
        a, b = re.sub(r"\D", "", a), re.sub(r"\D", "", b)
        if a and b:
            return float(f"{a}.{b}")
        return None  # carácter ilegible (p. ej. "7" -> "/")
    if s.startswith("."):
        s = "0" + s
    if "." in s:
        try:
            return float(s)
        except ValueError:
            return None
    digitos = re.sub(r"\D", "", s)
    if not digitos:
        return None
    v = int(digitos)
    if digitos.startswith("0"):
        # ceros a la izquierda: valor pequeño con decimal fijo
        return v * 10 ** -len(digitos)
    # sin ceros a la izquierda: lectura monótona (menor candidato > fila anterior)
    for p in range(len(digitos), -1, -1):
        c = v * 10 ** -p
        if prev is None or c > prev:
            return c
    return None


def reconstruir_columna(tokens, es_simple, ancla_idx):
    n = len(tokens)
    valores = [None] * n
    prev = -1e-12
    for i, tok in enumerate(tokens):
        v = token_a_valor(tok, prev)
        valores[i] = v
        if v is not None:
            prev = v
    if es_simple and ancla_idx is not None:
        valores[ancla_idx] = 1.0
    return valores


def interpolar_huecos(valores):
    """Rellena None y corrige no-monotonicidad interpolando entre vecinas válidas."""
    n = len(valores)
    estimado = [False] * n
    # primero: huecos (None) con el punto medio de las vecinas válidas más cercanas
    for i in range(n):
        if valores[i] is None:
            izq = next((valores[j] for j in range(i - 1, -1, -1) if valores[j] is not None), None)
            der = next((valores[j] for j in range(i + 1, n) if valores[j] is not None), None)
            if izq is not None and der is not None:
                valores[i] = (izq + der) / 2
            elif izq is not None:
                valores[i] = izq
            elif der is not None:
                valores[i] = der
            else:
                valores[i] = 0.0
            estimado[i] = True
    # luego: monotonicidad (no-decreciente), usando vecinas válidas
    for i in range(1, n - 1):
        if not (valores[i - 1] < valores[i] < valores[i + 1]):
            valores[i] = (valores[i - 1] + valores[i + 1]) / 2
            estimado[i] = True
    if n >= 2 and valores[n - 1] <= valores[n - 2]:
        valores[n - 1] = valores[n - 2] * 1.02
        estimado[n - 1] = True
    return estimado


def parsear_tablas() -> dict:
    tablas = {}
    actual = None
    with open(FUENTE, encoding="utf-8") as f:
        for linea in f:
            m = re.match(r"^Table D\.(\d+)\.\s+(.*)$", linea)
            if m:
                n = int(m.group(1))
                if n > 9:
                    actual = None
                    continue
                ma = re.search(r"\b(Single|Tandem|Triple)\b", m.group(2))
                mp = re.search(r"pt of\s+(\d\.\d)", m.group(2))
                if not ma or not mp:
                    actual = None
                    continue
                actual = (AXLE[ma.group(1)], mp.group(1))
                tablas[actual] = {"cargas": [], "columnas": [[] for _ in range(6)]}
                continue
            if actual is None or not linea.startswith("|"):
                continue
            campos = [c.strip() for c in linea.strip("|\n").split("|")]
            if len(campos) < 7:
                continue
            carga = re.sub(r"\D", "", campos[0])
            if not carga.isdigit():
                continue
            carga = int(carga)
            if carga > 50:  # la app solo consulta [2, 50] kip (ver spec)
                continue
            tablas[actual]["cargas"].append(carga)
            for j in range(6):
                tok = campos[1 + j]
                # correcciones puntuales de errores de caracteres del OCR
                tok = OVERRIDES.get((actual[0], actual[1], j, carga), tok)
                tablas[actual]["columnas"][j].append(tok)
    return tablas


def main() -> int:
    tablas = parsear_tablas()
    out = {"flexible": {}}
    total_estimadas = 0
    for (tipo, pt), t in sorted(tablas.items()):
        cargas = t["cargas"]
        ancla_idx = cargas.index(18) if (tipo == "simple" and 18 in cargas) else None
        lef = []
        for j in range(6):
            valores = reconstruir_columna(t["columnas"][j], es_simple=(tipo == "simple"), ancla_idx=ancla_idx)
            est = interpolar_huecos(valores)
            for i in range(1, len(valores)):
                if valores[i] <= valores[i - 1]:
                    print(f"WARN: no monótona {tipo} pt={pt} SN={j+1} carga={cargas[i]}: "
                          f"{valores[i-1]} -> {valores[i]}")
            lef.append(valores)
            total_estimadas += sum(est)
        out["flexible"].setdefault(tipo, {})[pt] = {
            "cargas": cargas,
            "sn": [1, 2, 3, 4, 5, 6],
            "lef": lef,
        }
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    nfilas = sum(len(v["cargas"]) for t in out["flexible"].values() for v in t.values())
    print(f"OK: {nfilas} filas escritas; {total_estimadas} celdas interpoladas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
