import pytest

from pavimentos.lef import DatosInvalidos, cargar_lef, lef_eje

T = cargar_lef()


def test_ancla_simple_18kip():
    for pt in ("2.0", "2.5", "3.0"):
        for sn in (1, 2, 3, 4, 5, 6):
            assert lef_eje(T, "simple", float(pt), 18.0, sn) == pytest.approx(1.0, abs=1e-9)


def test_valores_practico3():
    assert lef_eje(T, "simple", 2.0, 2.0, 3) == pytest.approx(0.0002, abs=1e-4)
    assert lef_eje(T, "simple", 2.0, 4.0, 3) == pytest.approx(0.002, abs=1e-3)
    assert lef_eje(T, "simple", 2.0, 8.0, 3) == pytest.approx(0.036, abs=1e-3)
    assert lef_eje(T, "simple", 2.0, 14.0, 3) == pytest.approx(0.354, abs=1e-3)
    assert lef_eje(T, "simple", 2.0, 22.0, 3) == pytest.approx(2.35, abs=1e-2)
    assert lef_eje(T, "tandem", 2.0, 36.0, 3) == pytest.approx(1.38, abs=1e-2)
    assert lef_eje(T, "tridem", 2.0, 50.0, 3) == pytest.approx(1.20, abs=1e-2)


def test_valores_wiki_pt25_sn4():
    # valores verificados en la wiki (avance 1, pág. 16)
    assert lef_eje(T, "simple", 2.5, 4.0, 4) == pytest.approx(0.003, abs=1e-3)
    assert lef_eje(T, "simple", 2.5, 10.0, 4) == pytest.approx(0.102, abs=1e-3)
    assert lef_eje(T, "simple", 2.5, 16.0, 4) == pytest.approx(0.645, abs=1e-3)
    assert lef_eje(T, "simple", 2.5, 30.0, 4) == pytest.approx(6.8, abs=1e-1)
    assert lef_eje(T, "tandem", 2.5, 34.0, 4) == pytest.approx(1.11, abs=1e-2)
    assert lef_eje(T, "tandem", 2.5, 36.0, 4) == pytest.approx(1.38, abs=1e-2)
    assert lef_eje(T, "tridem", 2.5, 48.0, 4) == pytest.approx(1.069, abs=1e-3)


def test_interpolacion_sn():
    # entre SN=2 y SN=3 para simple 22 kip, pt=2.0: 2.44 y 2.35
    v = lef_eje(T, "simple", 2.0, 22.0, 2.5)
    assert v == pytest.approx(2.395, abs=1e-2)


def test_monotonia_carga():
    for sn in (1, 3, 6):
        vals = [lef_eje(T, "simple", 2.5, c, sn) for c in range(2, 51, 2)]
        assert all(b >= a for a, b in zip(vals, vals[1:]))


def test_sn_fuera_de_rango():
    with pytest.raises(DatosInvalidos):
        lef_eje(T, "simple", 2.0, 18.0, 7.0)


def test_carga_fuera_de_rango():
    with pytest.raises(DatosInvalidos):
        lef_eje(T, "simple", 2.0, 60.0, 3)


def test_todas_las_columnas_monotonas():
    for tipo in ("simple", "tandem", "tridem"):
        for pt in ("2.0", "2.5", "3.0"):
            bloque = T["flexible"][tipo][pt]
            for j, col in enumerate(bloque["lef"]):
                assert all(b >= a for a, b in zip(col, col[1:])), \
                    f"columna no monótona {tipo} pt={pt} SN={j+1}"


def test_celdas_reconstruidas_correctas():
    # celdas que un OCR corrupto dejaba mal (revisión final)
    assert lef_eje(T, "tridem", 2.0, 2.0, 4) == pytest.approx(0.0000, abs=1e-5)
    assert lef_eje(T, "tridem", 2.0, 4.0, 4) == pytest.approx(0.0001, abs=1e-5)
    assert lef_eje(T, "tridem", 3.0, 4.0, 5) == pytest.approx(0.0001, abs=1e-5)
    assert lef_eje(T, "tridem", 3.0, 4.0, 6) == pytest.approx(0.0001, abs=1e-5)


def test_tandem_y_tridem_hasta_90_kip():
    # valores leídos de las tablas escaneadas D.2 y D.3 (AASHTO 93, pt = 2,0)
    assert lef_eje(T, "tandem", 2.0, 90.0, 1) == pytest.approx(94.4, abs=0.05)
    assert lef_eje(T, "tandem", 2.0, 80.0, 4) == pytest.approx(42.5, abs=0.05)
    assert lef_eje(T, "tridem", 2.0, 90.0, 6) == pytest.approx(15.2, abs=0.05)
    assert lef_eje(T, "tridem", 2.0, 60.0, 3) == pytest.approx(2.59, abs=0.01)


def test_simple_sigue_limitado_a_50_kip():
    with pytest.raises(DatosInvalidos):
        lef_eje(T, "simple", 2.0, 52.0, 3)
