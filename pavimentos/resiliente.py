"""Módulo 2 — Módulo resiliente efectivo de la subrasante (AASHTO '93)."""


class DatosInvalidos(ValueError):
    """Dato de entrada fuera de rango o inválido."""


def mr_de_cbr(cbr: float) -> float:
    """M_R (psi) a partir de CBR (%). Correlaciones de la guía AASHTO."""
    if cbr < 0 or cbr > 20:
        raise DatosInvalidos(f"CBR fuera del rango de la correlación (0-20%): {cbr}")
    if cbr < 7.2:
        return 1500.0 * cbr
    return 3000.0 * cbr ** 0.65


def danio_relativo(mr: float) -> float:
    """Daño relativo u_f = 1.18e8 * M_R^-2.32."""
    return 1.18e8 * mr ** -2.32


def mr_efectivo(periodos: list[dict]) -> dict:
    """M_R efectivo por daño relativo promedio ponderado por meses.

    Cada período: {"nombre": str, "meses": int, "mr": float}.
    Devuelve {"uf_bar": float, "mr_efectivo": float}.
    """
    total_meses = sum(p["meses"] for p in periodos)
    if total_meses != 12:
        raise DatosInvalidos(f"Los meses deben sumar 12 (suman {total_meses}).")
    uf_bar = sum(p["meses"] * danio_relativo(p["mr"]) for p in periodos) / 12.0
    mr_ef = (uf_bar / 1.18e8) ** (-1 / 2.32)
    return {"uf_bar": uf_bar, "mr_efectivo": mr_ef}
