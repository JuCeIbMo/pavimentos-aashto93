"""Gráficos estáticos (matplotlib) para el PDF."""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from pavimentos.formato import auto  # noqa: E402

ACENTO = "#C98A00"
OSCURO = "#1F2937"
GRIS = "#9CA3AF"


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def tornado_png(filas: list[dict], variacion: float) -> bytes:
    filas = list(reversed(filas))
    sn0 = filas[0]["sn_base"] if filas else 0
    fig, ax = plt.subplots(figsize=(6.4, 0.45 * len(filas) + 1.0))
    for i, f in enumerate(filas):
        lo, hi = f["sn_lo"] - sn0, f["sn_hi"] - sn0
        ax.barh(i, lo, color=GRIS, height=0.6)
        ax.barh(i, hi, color=ACENTO, height=0.6)
        ax.text(min(lo, hi) - 0.01, i, auto(min(f["sn_lo"], f["sn_hi"])), va="center", ha="right", fontsize=7)
        ax.text(max(lo, hi) + 0.01, i, auto(max(f["sn_lo"], f["sn_hi"])), va="center", ha="left", fontsize=7)
    ax.set_yticks(range(len(filas)), [f["etiqueta"] for f in filas], fontsize=8)
    ax.axvline(0, color=OSCURO, lw=0.8)
    ax.set_xlabel(f"Cambio del SN requerido (base = {auto(sn0)})", fontsize=8)
    ax.tick_params(axis="x", labelsize=7)
    ax.set_title(f"Sensibilidad del SN a una variación de ±{variacion * 100:.0f} %  "
                 "(gris: −, ámbar: +)", fontsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    margen = max((abs(f["sn_hi"] - sn0) for f in filas), default=0.1)
    margen = max(margen, max((abs(f["sn_lo"] - sn0) for f in filas), default=0.1))
    ax.set_xlim(-margen * 1.5 - 0.05, margen * 1.5 + 0.05)
    return _png(fig)


def curva_png(puntos: list[dict], etiqueta_x: str, x0: float | None, log_x: bool = False) -> bytes:
    pts = [p for p in puntos if p.get("sn_requerido") is not None]
    fig, ax1 = plt.subplots(figsize=(6.4, 3.0))
    xs = [p["x"] for p in pts]
    ax1.plot(xs, [p["sn_requerido"] for p in pts], color=OSCURO, lw=1.8, label="SN requerido")
    ax1.set_xlabel(etiqueta_x, fontsize=8)
    ax1.set_ylabel("SN requerido", fontsize=8)
    ax2 = ax1.twinx()
    unidad = pts[0]["unidad"] if pts else ""
    ax2.step(xs, [p["espesor_total"] for p in pts], where="mid", color=ACENTO, lw=1.4,
             label=f"Espesor total ({unidad})")
    ax2.set_ylabel(f"Espesor total ({unidad})", fontsize=8, color=ACENTO)
    if log_x:
        ax1.set_xscale("log")
    if x0 is not None:
        ax1.axvline(x0, color=GRIS, ls="--", lw=0.9)
    for a in (ax1, ax2):
        a.tick_params(labelsize=7)
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    return _png(fig)
