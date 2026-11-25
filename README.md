# Pavimentos AASHTO '93 (flexibles)

Paquete computacional de diseño de **pavimentos flexibles** por el método
AASHTO 1993. Motor de cálculo en Python, API con FastAPI e interfaz web con React.

## Módulos

- **1 · Tránsito**: ejes equivalentes (ESAL / W18). Por ejes con LEF tabulados (cargas en t o kip, conversión exacta
  1 t = 2,2046 kip o la de cátedra ×2) o con factor de camión conocido; tasa de crecimiento por vehículo.
- **2 · Subrasante**: M_R efectivo por daño relativo (meses, quincenas o estaciones; desde CBR o M_R directo).
- **4 · Diseño flexible**: SN requerido, coeficientes de capa, drenaje, espesores con mínimos AASHTO y verificaciones.
- **6 · Clima**: período de desempeño por hinchamiento y helada (iterativo, AASHTO 93, Apéndice G).
- **Sensibilidad y escenarios**: curva de una variable, diagrama tornado y comparación de hasta 3 alternativas.
- **Validación**: 4 ejercicios (práctico 3, examen 1, Apéndice H de la guía y Anexo V de Cabezas, 2006), 45/45 valores.
- **Exportación**: memoria de cálculo en PDF (Typst) y libro Excel con fórmulas vivas (el SN se resuelve
  por bisección en celdas). El proyecto se guarda y abre como `.json`.

Los módulos están conectados: el diseño toma el W18 del módulo 1 y el M_R del módulo 2 (o un dato, si se elige).

## Instalación

Requiere Python 3.11+ con [`uv`](https://docs.astral.sh/uv/) y Node 20+ con `pnpm`.

```bash
uv sync --extra dev
cd web && pnpm install
```

## Uso

```bash
./run.sh          # compila la interfaz si hace falta y abre http://localhost:8000
./run.sh dev      # desarrollo: API con recarga (8000) + Vite (http://localhost:5173)
```

## Despliegue (Docker)

```bash
docker compose up -d --build     # la app queda en el puerto 8000
```

Una sola imagen: compila la interfaz React y la sirve desde FastAPI junto con la API.
En el VPS conviene poner un proxy (Caddy o Nginx) con tu dominio y HTTPS delante del puerto 8000.

## Tests

```bash
uv run pytest
```

La suite resuelve los 4 ejercicios de `data/validacion/` y compara cada valor con su fuente;
también prueba la exportación PDF/Excel y la API.

## Estructura

- `pavimentos/`: motor de cálculo (Python puro; es la lógica que se explica en la defensa).
  - `modelo.py`: datos del proyecto · `resolver.py`: cadena 1→2→4→6 con decisiones y avisos.
  - `sensibilidad.py`, `validacion.py`, `referencias.py`.
  - `exportar_pdf.py` + `plantillas/memoria.typ`, `exportar_excel.py`.
- `api/main.py`: API FastAPI que expone el motor (resolver, ejemplos, validación, sensibilidad, PDF, Excel).
- `web/`: interfaz React + TypeScript + Tailwind (`src/paginas/` una página por módulo).
- `data/lef.json`: tablas LEF D.1–D.9 · `data/validacion/NN_*.json`: ejercicios de validación.
- `tests/`: validación, resolver, exportaciones y API.

## Notas

- Entrada en unidades SI (CBR %, kg/cm², cm, t) y cálculo interno en
  AASHTO (psi, pulg, kip); la interfaz muestra ambos sistemas.
- Las tablas LEF se reconstruyeron del OCR del Apéndice D (que perdió los
  puntos decimales), con control de monotonicidad y ancla 18 kip = 1,00.
  Los valores usados en el práctico 3 están verificados. Tándem y trídem se extendieron hasta 90 kip
  con la ecuación de AASHTO que genera esas tablas, verificada contra las tablas D.2 y D.3 escaneadas.
