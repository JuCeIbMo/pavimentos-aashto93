"""Formato numérico en español (miles con punto, decimales con coma)."""

from __future__ import annotations


def num(x, dec: int = 2) -> str:
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "sí" if x else "no"
    if not isinstance(x, (int, float)):
        return str(x)
    s = f"{x:,.{dec}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def entero(x) -> str:
    return num(x, 0)


def pct(x, dec: int = 1) -> str:
    return "—" if x is None else f"{num(x, dec)} %"


def auto(x) -> str:
    """Decimales razonables según la magnitud."""
    if x is None:
        return "—"
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        return num(x)
    a = abs(x)
    if a >= 1000:
        return num(x, 0)
    if a >= 100:
        return num(x, 1)
    if a >= 1:
        return num(x, 2)
    if a == 0:
        return "0"
    return num(x, 4)


def g(x) -> str:
    """Número corto sin ceros sobrantes (equivalente a :g con coma decimal)."""
    s = num(x, 3)
    if "," in s:
        s = s.rstrip("0").rstrip(",")
    return s
