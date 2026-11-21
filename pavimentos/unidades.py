"""Conversiones entre unidades SI (curso) y AASHTO (sistema inglés)."""

KG_CM2_A_PSI = 14.2233
CM_POR_PULG = 2.54
T_A_KIP = 2.0


def kg_cm2_a_psi(x: float) -> float:
    """kg/cm² → psi."""
    return x * KG_CM2_A_PSI


def cm_a_pulg(x: float) -> float:
    """Centímetros → pulgadas."""
    return x / CM_POR_PULG


def pulg_a_cm(x: float) -> float:
    """Pulgadas → centímetros."""
    return x * CM_POR_PULG


def t_a_kip(x: float) -> float:
    """Toneladas → kips (1 t ≈ 2 kip)."""
    return x * T_A_KIP
