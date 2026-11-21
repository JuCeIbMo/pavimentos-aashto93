from pavimentos.unidades import kg_cm2_a_psi, cm_a_pulg, pulg_a_cm, t_a_kip


def test_conversiones_exactas():
    assert kg_cm2_a_psi(1.0) == 14.2233
    assert cm_a_pulg(2.54) == 1.0
    assert pulg_a_cm(1.0) == 2.54
    assert t_a_kip(1.0) == 2.0


def test_redondeos_reales():
    assert round(kg_cm2_a_psi(29880), 0) == 424992
    assert round(cm_a_pulg(13), 2) == 5.12
