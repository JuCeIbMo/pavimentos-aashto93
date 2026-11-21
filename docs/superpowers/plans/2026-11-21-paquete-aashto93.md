# Paquete AASHTO '93 (flexibles) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un paquete computacional Streamlit que diseña pavimentos flexibles por AASHTO 1993 (módulos 1, 2, 4 y 6), validado con el práctico 3.

**Architecture:** Motor de cálculo puro en `pavimentos/` (solo stdlib, funciones puras), datos LEF en `data/lef.json`, interfaz delgada en `app/`. Cada módulo resuelve sus fórmulas ya verificadas en la wiki; la validación se fija con tests `pytest` de valores dorados del práctico 3.

**Tech Stack:** Python 3.13 (venv con `uv`), Streamlit, pytest. Sin numpy/scipy.

**Spec:** `docs/superpowers/specs/2026-11-21-paquete-aashto93-design.md`

## Global Constraints

- Motor (`pavimentos/`) sin imports de Streamlit, numpy ni scipy: solo stdlib.
- Entrada SI → cálculo AASHTO → salida dual. Conversiones fijas: `1 kg/cm² = 14.2233 psi`, `1 pulg = 2.54 cm`, `1 t = 2 kip`.
- Resolver `SN` por bisección en `[0.5, 10]`, tolerancia `1e-6`.
- Iteración `SN`↔`LEF` por punto fijo: opcional, máx. 5 vueltas, tolerancia `0.01`.
- Errores con excepciones propias `DatosInvalidos` (bloqueante) y `NoConverge`; advertencias no bloqueantes para el resto.
- Tolerancias de validación: ±0.5 % en `M_R` y `W`; ±0.02 en `SN`; exacto en espesores tras redondeo; ±0.1 en el período.
- Helada: coeficiente `0.02` editable y marcado "pendiente de verificar".
- Python 3.13 en venv de `uv`; dependencias: `streamlit`, `pytest`.
- Nombres y textos de la interfaz en español; coma decimal en la interfaz, punto en el código.

## Review Focus

Los cinco casos que el spec no cubre con un test explícito y que más probablemente rompan a un usuario:

1. **CBR > 20 % en el módulo 2**: la correlación CBR→M_R no aplica; debe lanzar `DatosInvalidos`, no extrapolar en silencio. → Task 3.
2. **Tasa de crecimiento r = 0**: `factor_crecimiento` debe devolver `n`, sin división por cero. → Task 4.
3. **SN fuera de [1, 6] en el lookup LEF**: debe lanzar `DatosInvalidos` con mensaje claro. → Task 2.
4. **Carga de eje fuera de [2, 50] kip**: debe lanzar `DatosInvalidos`. → Task 2.
5. **ΔPSI remanente ≤ 0 en el módulo 6** (el ambiente consume toda la serviciabilidad): debe lanzar `DatosInvalidos` explicativo. → Task 6.

---

## Estructura de archivos

- `pavimentos/unidades.py` — conversiones SI↔AASHTO.
- `pavimentos/lef.py` — carga de `data/lef.json` y lookup con interpolación bilineal.
- `pavimentos/resiliente.py` — M_R de CBR, daño relativo, M_R efectivo.
- `pavimentos/trafico.py` — crecimiento, factor de camión, ESAL, `w_t(t)`.
- `pavimentos/flexible.py` — Z_R, ecuación AASHTO, resolución de SN, espesores.
- `pavimentos/ambiental.py` — hinchamiento, helada, período de desempeño.
- `pavimentos/proyecto.py` — dataclasses `Proyecto`/`Vehiculo`/`Eje` y guardar/cargar JSON.
- `pavimentos/reporte.py` — HTML autocontenido imprimible.
- `scripts/parse_lef_docling.py` — genera `data/lef.json` a partir de `lefs_docling.md`.
- `data/lef.json` — matrices D.1–D.9.
- `data/validacion/practico3.json` — preset del práctico 3.
- `app/app.py` y `app/ui/*.py` — interfaz Streamlit.
- `tests/*.py` — suite.

---

### Task 0: Scaffolding del repositorio

**Files:**
- Create: `pyproject.toml`, `README.md`, `.gitignore`
- Create: directorios `pavimentos/`, `app/ui/`, `scripts/`, `data/`, `data/validacion/`, `tests/`

**Interfaces:**
- Produces: venv con Python 3.13 y dependencias `streamlit`+`pytest`; repo git inicializado.

- [ ] **Step 1: Crear `pyproject.toml`**

```toml
[project]
name = "pavimentos-aashto93"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["streamlit"]

[project.optional-dependencies]
dev = ["pytest"]
```

- [ ] **Step 2: Crear venv e instalar**

Run: `uv venv --python 3.13 .venv && uv pip install -e ".[dev]"`
Expected: sale `Installed` sin errores.

- [ ] **Step 3: Inicializar git y primeros archivos**

Run: `git init && printf '__pycache__/\n.venv/\n*.pyc\n' > .gitignore`
Write `README.md` con una línea: "Paquete computacional de diseño de pavimentos flexibles (AASHTO 93)."

- [ ] **Step 4: Verificar**

Run: `uv run python -c "import streamlit, pytest; print('ok')"`
Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: scaffolding del proyecto"
```

---

### Task 1: Conversiones de unidades

**Files:**
- Create: `pavimentos/unidades.py`
- Test: `tests/test_unidades.py`

**Interfaces:**
- Produces: `kg_cm2_a_psi(x: float) -> float`, `cm_a_pulg(x: float) -> float`, `pulg_a_cm(x: float) -> float`, `t_a_kip(x: float) -> float`.

- [ ] **Step 1: Escribir el test que falla**

```python
from pavimentos.unidades import kg_cm2_a_psi, cm_a_pulg, pulg_a_cm, t_a_kip

def test_conversiones_exactas():
    assert kg_cm2_a_psi(1.0) == 14.2233
    assert cm_a_pulg(2.54) == 1.0
    assert pulg_a_cm(1.0) == 2.54
    assert t_a_kip(1.0) == 2.0

def test_redondeos_reales():
    assert round(kg_cm2_a_psi(29880), 0) == 424992
    assert round(cm_a_pulg(13), 2) == 5.12
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `uv run pytest tests/test_unidades.py -v`
Expected: FAIL (`ModuleNotFoundError: pavimentos.unidades`).

- [ ] **Step 3: Implementar las cuatro funciones en `pavimentos/unidades.py`**

Constantes exactas: `KG_CM2_A_PSI = 14.2233`, `CM_POR_PULG = 2.54`, `T_A_KIP = 2.0`.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `uv run pytest tests/test_unidades.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pavimentos/unidades.py tests/test_unidades.py
git commit -m "feat: conversiones de unidades SI/AASHTO"
```

---

### Task 2: Datos LEF y lookup

**Files:**
- Create: `scripts/parse_lef_docling.py`, `pavimentos/lef.py`
- Create: `data/lef.json` (generado)
- Test: `tests/test_lef.py`

**Interfaces:**
- Consumes: `pavimentos.unidades.t_a_kip`.
- Produces:
  - `cargar_lef(ruta: str = "data/lef.json") -> dict` — estructura `{"flexible": {tipo_eje: {pt: {"cargas": list[float], "sn": list[int], "lef": list[list[float]]}}}}` con `tipo_eje ∈ {"simple","tandem","tridem"}` y `pt ∈ {"2.0","2.5","3.0"}`.
  - `lef_eje(tablas: dict, tipo_eje: str, pt: float, carga_kip: float, sn: float) -> float` — interpolación bilineal en (carga, sn); lanza `DatosInvalidos` si `sn ∉ [1,6]` o `carga_kip ∉ [2,50]`.

- [ ] **Step 1: Escribir el test que falla (valores del práctico 3 + reglas)**

```python
import pytest
from pavimentos.lef import cargar_lef, lef_eje, DatosInvalidos

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
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `uv run pytest tests/test_lef.py -v`
Expected: FAIL (`DatosInvalidos`/`cargar_lef` no definidos).

- [ ] **Step 3: Implementar `scripts/parse_lef_docling.py`**

Fuente: `~/Documentos/Uni/diseño-pavimentos/wiki/fuentes_texto/lefs_docling.md`.
Solo tablas D.1–D.9 (título "Table D.N." con N ≤ 9). Para cada celda:
1. Normalizar el token a su cadena de dígitos (quitar espacios y puntos).
2. Probar las posiciones del punto decimal (`int(digitos) × 10^-p`) y elegir la que cumpla, dentro de su columna (SN): monotonicidad no decreciente con la carga, continuidad suave con la fila anterior, y el ancla `18 kip = 1.00` para ejes simples.
3. Si dos posiciones son igual de válidas, marcar la celda `dudoso` y revisarla contra la imagen de la página (`pdftoppm` del `lefs.pdf`).
Escribir `data/lef.json` con el esquema de `cargar_lef`. Terminar con una auto-verificación: cada columna monótona y ancla exacta; si falla, imprimir la celda y abortar.

- [ ] **Step 4: Implementar `pavimentos/lef.py`**

`DatosInvalidos` hereda de `ValueError`. `cargar_lef` carga el JSON. `lef_eje` valida rangos, indexa el bloque `(tipo_eje, pt)`, y hace interpolación bilineal en (carga, sn) usando `math`.

- [ ] **Step 5: Correr y verificar que pasa**

Run: `uv run pytest tests/test_lef.py -v`
Expected: PASS (si alguna celda dudosa persistió, revisarla y corregir `data/lef.json`).

- [ ] **Step 6: Commit**

```bash
git add scripts/parse_lef_docling.py pavimentos/lef.py data/lef.json tests/test_lef.py
git commit -m "feat: tablas LEF D.1-D.9 y lookup con interpolacion"
```

---

### Task 3: Módulo 2 — M_R efectivo

**Files:**
- Create: `pavimentos/resiliente.py`
- Test: `tests/test_resiliente.py`

**Interfaces:**
- Produces:
  - `mr_de_cbr(cbr: float) -> float` — `1500*CBR` si `CBR < 7.2`; `3000*CBR**0.65` si `7.2 <= CBR <= 20`; `DatosInvalidos` si `CBR > 20` o `CBR < 0`.
  - `danio_relativo(mr: float) -> float` — `1.18e8 * mr**-2.32`.
  - `mr_efectivo(periodos: list[dict]) -> dict` — cada período `{"nombre": str, "meses": int, "mr": float}`; devuelve `{"uf_bar": float, "mr_efectivo": float}`. Si `sum(meses) != 12`, lanza `DatosInvalidos`.

- [ ] **Step 1: Escribir el test que falla**

```python
import pytest
from pavimentos.resiliente import mr_de_cbr, danio_relativo, mr_efectivo, DatosInvalidos

def test_mr_de_cbr_bajo():
    assert mr_de_cbr(4.7) == pytest.approx(7050, abs=0.5)
def test_mr_de_cbr_alto():
    assert mr_de_cbr(13.1) == pytest.approx(15972, abs=0.5)
def test_mr_de_cbr_fuera_de_rango():
    with pytest.raises(DatosInvalidos):
        mr_de_cbr(21.0)

def test_danio_relativo():
    assert danio_relativo(7050) == pytest.approx(0.1393, abs=1e-4)

PERIODOS = [
    {"nombre": "Ene-Mar", "meses": 3, "mr": 7050},
    {"nombre": "Abr", "meses": 1, "mr": 10050},
    {"nombre": "May/Nov/Dic", "meses": 3, "mr": 11965},
    {"nombre": "Jun-Oct", "meses": 5, "mr": 15972},
]

def test_mr_efectivo_practico3():
    r = mr_efectivo(PERIODOS)
    assert r["uf_bar"] == pytest.approx(0.0589, abs=1e-4)
    assert r["mr_efectivo"] == pytest.approx(10222, rel=0.005)

def test_meses_no_suman_12():
    with pytest.raises(DatosInvalidos):
        mr_efectivo(PERIODOS[:2])
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `uv run pytest tests/test_resiliente.py -v`
Expected: FAIL.

- [ ] **Step 3: Implementar `pavimentos/resiliente.py`**

`mr_efectivo`: `uf_bar = sum(p["meses"]*danio_relativo(p["mr"]) for p in periodos)/12`; `mr_efectivo = (uf_bar/1.18e8)**(-1/2.32)`.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `uv run pytest tests/test_resiliente.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pavimentos/resiliente.py tests/test_resiliente.py
git commit -m "feat: modulo 2 - modulo resiliente efectivo"
```

---

### Task 4: Módulo 1 — Tránsito y ESAL

**Files:**
- Create: `pavimentos/trafico.py`
- Create: `data/validacion/practico3.json`
- Test: `tests/test_trafico.py`

**Interfaces:**
- Consumes: `pavimentos.lef.lef_eje`, `pavimentos.unidades.t_a_kip`.
- Produces:
  - `factor_crecimiento(r: float, n: float) -> float` — `((1+r)**n - 1)/r`, con `r == 0 → n`.
  - `factor_camion(vehiculo: dict, tablas: dict, pt: float, sn: float) -> float`.
  - `esal_vehiculo(vehiculo: dict, n: float, fd: float, fc: float, tablas: dict, pt: float, sn: float) -> dict` → `{"fc", "esal1", "w"}`.
  - `esal_total(vehiculos: list[dict], n: float, fd: float, fc: float, tablas: dict, pt: float, sn: float) -> dict` → `{"total_w", "total_esal1", "tpda_total", "pesados_pct", "por_vehiculo"}`.
  - `w_t(vehiculos, t: float, fd, fc, tablas, pt, sn) -> float` — suma de `esal1_i * factor_crecimiento(r_i, t)`.
  - `Vehiculo` se representa como dict `{"nombre", "tpda", "r", "pesado", "ejes": [[tipo, carga_t], ...]}`.

- [ ] **Step 1: Crear `data/validacion/practico3.json`**

`{"nombre":"Practico 3","n":15,"fd":0.5,"fc":1.0,"sn":3,"pt":2.0,"vehiculos":[...]}` con estos 12 vehículos (`ejes` = pares `[tipo, carga_t]`; `1 t = 2 kip`):

| nombre | tpda | r | pesado | ejes |
|---|---|---|---|---|
| Automóvil | 250 | 0.03 | false | [simple,1],[simple,1] |
| Camioneta | 65 | 0.03 | false | [simple,1],[simple,2] |
| Minibús | 315 | 0.03 | false | [simple,1],[simple,2] |
| Bus 12-21 | 1 | 0.03 | true | [simple,1],[simple,4] |
| Bus 21-35 | 25 | 0.05 | true | [simple,2],[simple,11] |
| Bus 35+ | 35 | 0.04 | true | [simple,7],[tandem,18] |
| Camión mediano | 32 | 0.02 | true | [simple,7],[simple,11] |
| Camión grande 2 ejes | 16 | 0.02 | true | [simple,7],[tridem,25] |
| Camión grande 3 ejes | 8 | 0.01 | true | [simple,7],[simple,7],[tandem,18] |
| Semirremolque | 2 | 0.01 | true | [simple,7],[tridem,25],[tandem,18] |
| Camión con remolque | 1 | 0.01 | true | [simple,7],[simple,11],[tridem,25],[tandem,18] |
| Otros | 4 | 0.03 | false | [simple,1],[simple,4] |

- [ ] **Step 2: Escribir el test que falla**

```python
import json, pytest
from pavimentos.lef import cargar_lef
from pavimentos.trafico import factor_crecimiento, factor_camion, esal_vehiculo, esal_total, w_t

T = cargar_lef()
with open("data/validacion/practico3.json") as f:
    P = json.load(f)

def test_factor_crecimiento():
    assert factor_crecimiento(0.02, 15) == pytest.approx(17.293, abs=1e-2)
    assert factor_crecimiento(0.03, 20) == pytest.approx(26.87, abs=1e-2)
    assert factor_crecimiento(0.0, 15) == 15.0

CAMION = {"nombre":"Camión mediano","tpda":32,"r":0.02,"pesado":True,
          "ejes":[["simple",7],["simple",11]]}

def test_camion_mediano():
    r = esal_vehiculo(CAMION, 15, 0.5, 1.0, T, 2.0, 3)
    assert r["fc"] == pytest.approx(2.704, abs=1e-3)
    assert r["esal1"] == pytest.approx(15791, abs=1e-0)
    assert r["w"] == pytest.approx(273087, rel=0.005)

def test_total_practico3():
    r = esal_total(P["vehiculos"], 15, 0.5, 1.0, T, 2.0, 3)
    assert r["total_w"] == pytest.approx(890521, rel=0.005)

def test_w_t_continuo():
    assert w_t(P["vehiculos"], 15, 0.5, 1.0, T, 2.0, 3) == pytest.approx(890521, rel=0.005)
```

- [ ] **Step 3: Correr y verificar que falla**

Run: `uv run pytest tests/test_trafico.py -v`
Expected: FAIL.

- [ ] **Step 4: Implementar `pavimentos/trafico.py`**

`esal1 = tpda * factor_camion * 365 * fd * fc`; `w = esal1 * factor_crecimiento(r, n)`. `pesados_pct = 100 * sum(tpda de pesado)/tpda_total`. `w_t` evalúa en `t` real (admite no enteros).

- [ ] **Step 5: Correr y verificar que pasa**

Run: `uv run pytest tests/test_trafico.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pavimentos/trafico.py data/validacion/practico3.json tests/test_trafico.py
git commit -m "feat: modulo 1 - transito y ESAL"
```

---

### Task 5: Módulo 4 — Diseño de flexibles

**Files:**
- Create: `pavimentos/flexible.py`
- Test: `tests/test_flexible.py`

**Interfaces:**
- Consumes: `pavimentos.unidades.cm_a_pulg`, `pulg_a_cm`.
- Produces:
  - `zr_de_r(r_pct: float) -> float` — `-NormalDist().inv_cdf(r_pct/100)` (de `statistics`).
  - `r_etapa(r_global_pct: float, n_etapas: int) -> float` — `r_global**(1/n)`.
  - `log_w18(sn: float, zr: float, so: float, delta_psi: float, mr: float) -> float`.
  - `sn_requerido(w18: float, zr: float, so: float, delta_psi: float, mr: float) -> float` — bisección en `[0.5,10]`, tol `1e-6`.
  - `coef_a1(e_ca: float) -> float`, `coef_a2(e_b: float) -> float`, `coef_a3(e_sb: float) -> float`.
  - `disenar_capas(w18, zr, so, delta_psi, mr, e_b, e_sb, a1, a2, a3, m2=1.0, m3=1.0, min_ca_cm=0.0, min_base_cm=0.0, min_subbase_cm=0.0, redondeo_cm=0.5) -> dict` con claves `sn1, sn2, sn3, d1_cm, d2_cm, d3_cm, sn_total, cumple`.

- [ ] **Step 1: Escribir el test que falla**

```python
import pytest
from pavimentos.flexible import (zr_de_r, r_etapa, sn_requerido, log_w18,
                                 coef_a1, coef_a2, coef_a3, disenar_capas)

def test_zr():
    assert zr_de_r(90.0) == pytest.approx(-1.282, abs=1e-3)
    assert zr_de_r(85.0) == pytest.approx(-1.036, abs=1e-3)

def test_r_etapa():
    assert r_etapa(85.0, 2) == pytest.approx(92.195, abs=1e-2)

def test_coeficientes():
    assert coef_a1(400000) == pytest.approx(0.4175, abs=1e-4)
    assert coef_a2(30000) == pytest.approx(0.1378, abs=1e-4)
    assert coef_a3(11000) == pytest.approx(0.0785, abs=1e-4)

def test_sn_practico3():
    sn = sn_requerido(w18=890521, zr=-1.419, so=0.49, delta_psi=2.2, mr=10222)
    assert sn == pytest.approx(3.1, abs=0.02)

def test_capas_practico3():
    r = disenar_capas(
        w18=859000, zr=-1.419, so=0.49, delta_psi=1.888, mr=10222,
        e_b=28143, e_sb=16199, a1=0.428, a2=0.131, a3=0.117,
        m2=1.0, m3=1.0, min_ca_cm=7.5, min_base_cm=15.0, min_subbase_cm=10.0)
    assert r["sn3"] == pytest.approx(3.10, abs=0.02)
    assert r["d1_cm"] == 13.0
    assert r["d2_cm"] == 15.0
    assert r["d3_cm"] == 10.0
    assert r["cumple"] is True
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `uv run pytest tests/test_flexible.py -v`
Expected: FAIL.

- [ ] **Step 3: Implementar `pavimentos/flexible.py`**

`log_w18` implementa la ecuación de la spec §5.3 (constantes `9.36, -0.20, 1094, 5.19, 2.32, -8.07`). `sn_requerido` usa `log_w18(sn) == log10(w18)`. `disenar_capas` sigue el procedimiento por capas de la spec: `sn1 = sn_requerido(w18, zr, so, delta_psi, e_b)`, `sn2 = sn_requerido(w18, zr, so, delta_psi, e_sb)`, `sn3 = sn_requerido(w18, zr, so, delta_psi, mr)`; luego `d1 = max(redondear_arriba(sn1/a1), min_ca_cm)`, aportes `sn1* = a1*d1/2.54`, etc.; `sn_total = sn1*+sn2*+sn3*`, `cumple = sn_total >= sn3`.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `uv run pytest tests/test_flexible.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pavimentos/flexible.py tests/test_flexible.py
git commit -m "feat: modulo 4 - SN y espesores flexibles"
```

---

### Task 6: Módulo 6 — Clima y período de desempeño

**Files:**
- Create: `pavimentos/ambiental.py`
- Test: `tests/test_ambiental.py`

**Interfaces:**
- Consumes: `pavimentos.flexible.log_w18`.
- Produces:
  - `delta_psi_hinchamiento(vr: float, ps: float, theta: float, t: float) -> float`.
  - `delta_psi_helada(pf: float, dpsi_max: float, phi: float, t: float, coef: float = 0.02) -> float`.
  - `periodo_desempeno(sn: float, mr: float, delta_psi_total: float, zr: float, so: float, vr: float, ps: float, theta: float, t_inicial: float, w_t_fn: callable, helada: dict | None = None) -> dict` → `{"periodo": float, "w_adm": float, "iteraciones": list[dict], "dpsi_sw": float, "dpsi_tr": float}`.

- [ ] **Step 1: Escribir el test que falla**

```python
import pytest
from pavimentos.ambiental import delta_psi_hinchamiento, delta_psi_helada, periodo_desempeno, DatosInvalidos

def test_hinchamiento():
    assert delta_psi_hinchamiento(2.0, 60.0, 0.1, 15) == pytest.approx(0.312, abs=1e-3)

def test_helada_formula():
    assert delta_psi_helada(50.0, 1.0, 20.0, 10) == pytest.approx(0.01*50*1*(1 - __import__("math").exp(-0.02*20*10)), abs=1e-9)

def test_periodo_simple():
    # w_t creciente; ambiente que deja margen
    w_t_fn = lambda t: 890521 * (1.02**t - 1) / (1.02**15 - 1)
    r = periodo_desempeno(sn=3.1, mr=10222, delta_psi_total=2.2, zr=-1.419, so=0.49,
                           vr=2.0, ps=60.0, theta=0.1, t_inicial=15, w_t_fn=w_t_fn)
    assert 0 < r["dpsi_tr"] < 2.2
    assert r["periodo"] > 0

def test_ambiente_consume_todo():
    with pytest.raises(DatosInvalidos):
        periodo_desempeno(sn=3.1, mr=10222, delta_psi_total=0.2, zr=-1.419, so=0.49,
                          vr=2.0, ps=60.0, theta=0.1, t_inicial=15, w_t_fn=lambda t: 1000)
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `uv run pytest tests/test_ambiental.py -v`
Expected: FAIL.

- [ ] **Step 3: Implementar `pavimentos/ambiental.py`**

`periodo_desempeno`: itera `t` (arranca en `t_inicial`): calcula `dpsi_sw` (+ helada si viene), `dpsi_tr = delta_psi_total - dpsi_env`; si `dpsi_tr <= 0` → `DatosInvalidos`; `w_adm = 10**log_w18(sn, zr, so, dpsi_tr, mr)`; invierte `t_calc = inversa(w_t_fn, w_adm)` por bisección en `[0, 2*t_inicial]`; si `|t - t_calc| < 1` converge y devuelve `(t + t_calc)/2`; si no, `t = (t + t_calc)/2` y repite (máx. 10).

- [ ] **Step 4: Correr y verificar que pasa**

Run: `uv run pytest tests/test_ambiental.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pavimentos/ambiental.py tests/test_ambiental.py
git commit -m "feat: modulo 6 - clima y periodo de desempeno"
```

---

### Task 7: Integración — validación completa del práctico 3

**Files:**
- Test: `tests/test_validacion_practico3.py`

**Interfaces:**
- Consumes: todo lo anterior (`cargar_lef`, `mr_efectivo`, `esal_total`, `w_t`, `sn_requerido`, `disenar_capas`, `periodo_desempeno`).
- Produces: la tabla de validación de la spec §7.

- [ ] **Step 1: Escribir el test end-to-end**

```python
import json, pytest
from pavimentos.lef import cargar_lef
from pavimentos.resiliente import mr_efectivo
from pavimentos.trafico import esal_total, w_t
from pavimentos.flexible import zr_de_r, r_etapa, sn_requerido, disenar_capas, coef_a1, coef_a2, coef_a3
from pavimentos.ambiental import periodo_desempeno

T = cargar_lef()
with open("data/validacion/practico3.json") as f:
    P = json.load(f)

PERIODOS = [
    {"nombre": "Ene-Mar", "meses": 3, "mr": 7050},
    {"nombre": "Abr", "meses": 1, "mr": 10050},
    {"nombre": "May/Nov/Dic", "meses": 3, "mr": 11965},
    {"nombre": "Jun-Oct", "meses": 5, "mr": 15972},
]

def test_practico3_completo():
    mr = mr_efectivo(PERIODOS)["mr_efectivo"]                      # 10222
    w15 = esal_total(P["vehiculos"], 15, 0.5, 1.0, T, 2.0, 3)["total_w"]  # 890521
    zr = zr_de_r(r_etapa(85.0, 2))                                # -1.419
    sn = sn_requerido(w15, zr, 0.49, 2.2, mr)                     # 3.1
    cap = disenar_capas(w15, zr, 0.49, 2.2, mr, 28143, 16199,
                        0.428, 0.131, 0.117, 1.0, 1.0, 7.5, 15.0, 10.0)
    r = periodo_desempeno(sn, mr, 2.2, zr, 0.49, 2.0, 60.0, 0.1, 15,
                          w_t_fn=lambda t: w_t(P["vehiculos"], t, 0.5, 1.0, T, 2.0, 3))

    assert mr == pytest.approx(10222, rel=0.005)
    assert w15 == pytest.approx(890521, rel=0.005)
    assert sn == pytest.approx(3.1, abs=0.02)
    assert (cap["d1_cm"], cap["d2_cm"], cap["d3_cm"]) == (13.0, 15.0, 10.0)
    assert r["periodo"] == pytest.approx(14.8, abs=0.1)
```

- [ ] **Step 2: Correr**

Run: `uv run pytest tests/test_validacion_practico3.py -v`
Expected: PASS (si falla, corregir el motor que corresponda, no aflojar tolerancias).

- [ ] **Step 3: Commit**

```bash
git add tests/test_validacion_practico3.py
git commit -m "test: validacion end-to-end del practico 3"
```

---

### Task 8: Proyecto y reporte

**Files:**
- Create: `pavimentos/proyecto.py`, `pavimentos/reporte.py`
- Test: `tests/test_proyecto.py`

**Interfaces:**
- Consumes: módulos 1–6.
- Produces:
  - `Proyecto` (dataclass): `nombre: str`, `trafico: dict | None`, `subrasante: dict | None`, `flexible: dict | None`, `clima: dict | None`.
  - `guardar_proyecto(proyecto, path)`, `cargar_proyecto(path) -> Proyecto`.
  - `generar_reporte_html(proyecto, resultados: dict) -> str` — HTML autocontenido con CSS de impresión A4.

- [ ] **Step 1: Escribir el test**

```python
import json, tempfile, os
from pavimentos.proyecto import Proyecto, guardar_proyecto, cargar_proyecto
from pavimentos.reporte import generar_reporte_html

def test_guardar_cargar_roundtrip():
    p = Proyecto(nombre="Prueba", trafico={"total_w": 890521}, subrasante={"mr_efectivo": 10222})
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "p.json")
        guardar_proyecto(p, path)
        q = cargar_proyecto(path)
    assert q.nombre == "Prueba"
    assert q.trafico["total_w"] == 890521

def test_reporte_html():
    p = Proyecto(nombre="Prueba")
    html = generar_reporte_html(p, {"trafico": {"total_w": 890521}})
    assert "<html" in html and "890" in html and "<table" in html
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `uv run pytest tests/test_proyecto.py -v`
Expected: FAIL.

- [ ] **Step 3: Implementar `proyecto.py` y `reporte.py`**

`guardar_proyecto` usa `dataclasses.asdict` + `json.dump`. `generar_reporte_html` concatena secciones con tablas HTML y un `@media print` básico; números con formato español (coma decimal) solo en la capa de presentación.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `uv run pytest tests/test_proyecto.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pavimentos/proyecto.py pavimentos/reporte.py tests/test_proyecto.py
git commit -m "feat: persistencia de proyecto y reporte HTML"
```

---

### Task 9: Interfaz Streamlit

**Files:**
- Create: `app/app.py`, `app/ui/{trafico,subrasante,flexibles,clima,validacion,componentes}.py`

**Interfaces:**
- Consumes: todos los motores + `Proyecto` + `generar_reporte_html`.

- [ ] **Step 1: Implementar `app/ui/componentes.py`** — helpers: input numérico con unidad, tarjeta de métrica, tabla, aviso de error/advertencia, `cargar_practico3()`.

- [ ] **Step 2: Implementar `app/app.py`** — sidebar con las páginas (Inicio, 1 Tránsito, 2 Subrasante, 4 Flexibles, 6 Clima, Validación, 7 Marshall deshabilitado) y `st.session_state["proyecto"]`.

- [ ] **Step 3: Implementar las cuatro páginas** — cada una: `st.form` de entrada → botón "Calcular" → resultados (tarjetas + tabla) → `st.expander("Procedimiento")` con ecuaciones y valores intermedios → botón "Guardar en proyecto". La página de Validación carga `practico3.json`, ejecuta los motores y muestra esperado vs. obtenido.

- [ ] **Step 4: Smoke test manual**

Run: `uv run streamlit run app/app.py`
Expected: abre el navegador; la página Validación muestra el práctico 3 todo en verde.

- [ ] **Step 5: Commit**

```bash
git add app/
git commit -m "feat: interfaz Streamlit y pagina de validacion"
```

---

### Task 10: Suite completa y cierre

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Correr toda la suite**

Run: `uv run pytest -q`
Expected: todos los tests PASS.

- [ ] **Step 2: Escribir `README.md`** — cómo instalar (`uv venv --python 3.13 .venv && uv pip install -e ".[dev]"`), correr (`uv run streamlit run app/app.py`) y testear (`uv run pytest`).

- [ ] **Step 3: Commit**

```bash
git add README.md && git commit -m "docs: README de uso"
```
