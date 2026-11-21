# Pavimentos AASHTO '93 (flexibles)

Paquete computacional de diseño de **pavimentos flexibles** por el método
AASHTO 1993, con interfaz Streamlit.

## Módulos

- **1 · Tránsito** — ejes equivalentes (ESAL / W18), factor de camión, crecimiento.
- **2 · Subrasante** — módulo resiliente efectivo y daño relativo.
- **4 · Flexibles** — número estructural (SN) y espesores de carpeta, base y subbase.
- **6 · Clima** — ajuste de vida útil por hinchamiento y helada.
- **7 · Marshall** — reservado (pendiente de implementar).

## Instalación

Requiere Python 3.11+ y [`uv`](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.13 .venv
uv pip install -e ".[dev]"
```

## Uso

```bash
uv run streamlit run app/app.py
```

## Tests

```bash
uv run pytest
```

La suite fija los valores del **práctico 3** (M_R efectivo = 10.222 psi,
W15 = 890.521 ESAL, SN = 3.1, espesores 13 / 15 / 10 cm, período con
hinchamiento = 14,8 años) como casos de validación.

## Estructura

- `pavimentos/` — motor de cálculo puro (solo stdlib, sin Streamlit).
- `app/` — interfaz Streamlit.
- `data/lef.json` — tablas LEF D.1–D.9 reconstruidas desde `lefs.pdf`.
- `data/validacion/practico3.json` — composición vehicular del práctico 3.
- `scripts/parse_lef_docling.py` — regenera `data/lef.json` una sola vez.
- `tests/` — suite de validación.

## Notas

- Entrada en unidades SI (CBR %, kg/cm², cm, t) y cálculo interno en
  AASHTO (psi, pulg, kip); la interfaz muestra ambos sistemas.
- Las tablas LEF se reconstruyeron del OCR del Apéndice D (que perdió los
  puntos decimales), con control de monotonicidad y ancla 18 kip = 1,00.
  Los valores usados en el práctico 3 están verificados.
