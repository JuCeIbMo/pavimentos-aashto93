# Pavimentos AASHTO '93 (flexibles)

Paquete computacional de diseño de **pavimentos flexibles** por el método
AASHTO 1993, con interfaz Streamlit.

## Módulos

- **1 · Tránsito**: ejes equivalentes (ESAL / W18). Por ejes con LEF tabulados o con factor de camión conocido.
- **2 · Subrasante**: M_R efectivo por daño relativo (meses, quincenas o estaciones; desde CBR o M_R directo).
- **4 · Diseño flexible**: SN requerido, coeficientes de capa, drenaje, espesores con mínimos AASHTO y verificaciones.
- **6 · Clima**: período de desempeño por hinchamiento y helada (iterativo, AASHTO 93, Apéndice G).
- **Sensibilidad y escenarios**: curva de una variable, diagrama tornado y comparación de hasta 3 alternativas.
- **Validación**: 4 ejercicios (práctico 3, examen 1, Apéndice H de la guía y Anexo V de Cabezas, 2006), 45/45 valores.
- **Exportación**: memoria de cálculo en PDF (Typst) y libro Excel con fórmulas vivas (el SN se resuelve
  por bisección en celdas). El proyecto se guarda y abre como `.json`.

Los módulos están conectados: el diseño toma el W18 del módulo 1 y el M_R del módulo 2 (o un dato, si se elige).

## Instalación

Requiere Python 3.11+ y [`uv`](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.13 .venv
uv pip install -e ".[dev]"
```

## Uso

```bash
./run.sh            # o: uv run streamlit run app/app.py
```

## Tests

```bash
uv run pytest
```

La suite resuelve los 4 ejercicios de `data/validacion/` y compara cada valor con su fuente;
también prueba la exportación PDF/Excel y que cada página de la interfaz cargue sin errores.

## Estructura

- `pavimentos/`: motor de cálculo (sin Streamlit).
  - `modelo.py`: datos del proyecto · `resolver.py`: cadena 1→2→4→6 con decisiones y avisos.
  - `sensibilidad.py`, `validacion.py`, `referencias.py`.
  - `exportar_pdf.py` + `plantillas/memoria.typ`, `exportar_excel.py`.
- `app/`: interfaz Streamlit (`app.py` y `ui/`).
- `data/lef.json`: tablas LEF D.1–D.9 · `data/validacion/NN_*.json`: ejercicios de validación.
- `tests/`: validación, resolver, exportaciones y prueba de humo de la interfaz.

## Notas

- Entrada en unidades SI (CBR %, kg/cm², cm, t) y cálculo interno en
  AASHTO (psi, pulg, kip); la interfaz muestra ambos sistemas.
- Las tablas LEF se reconstruyeron del OCR del Apéndice D (que perdió los
  puntos decimales), con control de monotonicidad y ancla 18 kip = 1,00.
  Los valores usados en el práctico 3 están verificados.
