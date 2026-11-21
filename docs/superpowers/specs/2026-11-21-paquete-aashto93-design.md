# Spec — Paquete computacional de diseño de pavimentos flexibles (AASHTO '93)

Fecha: 2026-11-21
Estado: borrador para revisión

## 1. Objetivo

Construir un paquete computacional (Python + Streamlit) que realice el diseño de
pavimentos **flexibles** por el método AASHTO 1993, con cuatro módulos
funcionales, validado contra el práctico 3 del curso, y que deje reservado el
espacio del módulo Marshall.

## 2. Alcance

**Incluido (esta etapa):**

- Módulo 1 — Cálculo de ejes equivalentes (ESAL / \(W_{18}\)).
- Módulo 2 — \(M_R\) efectivo de la subrasante y daño relativo.
- Módulo 4 — Diseño de pavimentos flexibles (SN y espesores).
- Módulo 6 — Ajuste de vida útil por hinchamiento y helada.
- Página de validación con el práctico 3.
- Reporte HTML imprimible y exportación CSV; guardar/cargar proyecto `.json`.

**Reservado (no implementar ahora):**

- Módulo 7 — Marshall: entrada en el menú deshabilitada.
- Módulos 3 y 5 — Pavimentos rígidos: fuera de alcance de esta entrega.

**Fuera de alcance:**

- Manual de usuario, memoria técnica y presentación (se escriben después,
  sobre la base ya validada).

## 3. Decisiones de diseño

| Tema | Decisión |
|---|---|
| Plataforma | Python + Streamlit |
| Unidades | Entrada SI (CBR %, kg/cm², cm, t) → cálculo AASHTO (psi, pulg, kip) → salida dual |
| LEF | Matrices tabulares AASHTO (D.1–D.9) + interpolación bilineal |
| Resolución de SN | Bisección en [0,5; 10], tolerancia 1e-6 |
| Iteración SN↔LEF | Punto fijo, opcional, máx. 5 vueltas, tolerancia 0,01 |
| Módulo 6 | Hinchamiento completo + helada con coeficiente editable (0,02, pendiente de verificar) |
| Reporte | HTML autocontenido imprimible (sin dependencias de PDF) |
| Validación | pytest con valores dorados del práctico 3 |

## 4. Arquitectura

```
proyecto-carreteras-ii/
├── pyproject.toml
├── README.md
├── app/
│   ├── app.py                  # entrada Streamlit (sidebar con módulos)
│   └── ui/
│       ├── trafico.py          # módulo 1
│       ├── subrasante.py       # módulo 2
│       ├── flexibles.py        # módulo 4
│       ├── clima.py            # módulo 6
│       ├── validacion.py
│       └── componentes.py      # inputs, tablas, tarjetas, avisos
├── pavimentos/                 # motor puro, SIN Streamlit, solo stdlib
│   ├── unidades.py
│   ├── lef.py
│   ├── trafico.py
│   ├── resiliente.py
│   ├── flexible.py
│   ├── ambiental.py
│   ├── proyecto.py             # dataclasses + guardar/cargar
│   └── reporte.py              # HTML imprimible
├── data/
│   ├── lef.json                # matrices D.1–D.9 reconstruidas
│   └── validacion/practico3.json
├── scripts/
│   └── parse_lef_docling.py    # genera data/lef.json una sola vez
└── tests/
    ├── test_lef.py
    ├── test_trafico.py
    ├── test_resiliente.py
    ├── test_flexible.py
    ├── test_ambiental.py
    └── test_validacion_practico3.py
```

Reglas del motor: funciones puras que reciben `dict`/`dataclass` y devuelven
resultados con unidades explícitas. Ningún cálculo importa Streamlit, numpy ni
scipy. Errores con excepciones propias (`DatosInvalidos`, `NoConverge`).

## 5. Especificación por módulo

### 5.1 Módulo 1 — Tránsito y ESAL

**Entrada:** período \(n\); \(F_d\); carriles por sentido → \(F_c\); \(SN\)
supuesto y \(p_t\) (2,0/2,5/3,0) para el LEF; tabla de vehículos (nombre,
TPDA, tasa \(r\), hasta 6 ejes con tipo y carga en t). Preset cargable con la
composición del práctico 3.

**Cálculo:**

- LEF por eje desde la matriz \((tipo, p_t)\) en \((carga, SN)\). Interpolación
  bilineal solo si el valor cae entre filas/columnas; si es exacto, lookup directo.
- \(FC=\sum LEF_{\text{ejes}}\)
- \(ESAL_1 = TPDA\cdot FC\cdot365\cdot F_d\cdot F_c\)
- \(W = ESAL_1\cdot\frac{(1+r)^n-1}{r}\) (con \(r=0\), factor \(=n\))
- Totales \(W_{18}\), \(\log W_{18}\), % de vehículos pesados.
- Expone \(W(t)\) para cualquier \(t\) (suma por vehículo), usado por 4 y 6.

**Validación:** práctico 3 → \(W_{15}=890\,521\) ESAL.

### 5.2 Módulo 2 — \(M_R\) efectivo

**Entrada:** períodos (nombre, meses, CBR **o** \(M_R\) directo). Los meses
deben sumar 12 (aviso + normalizar).

**Cálculo:**

- \(M_R=1500\,CBR\) si \(CBR<7{,}2\); \(M_R=3000\,CBR^{0{,}65}\) si \(7{,}2\le CBR\le20\).
  Si \(CBR>20\): error (correlación no válida), pedir \(M_R\) directo.
- \(u_f=1{,}18\times10^{8}\,M_R^{-2{,}32}\)
- \(\bar u_f=\sum m_i u_{f,i}/12\)
- \(M_{R,ef}=(\bar u_f/1{,}18\times10^{8})^{-1/2{,}32}\)

**Validación:** práctico 3 → \(M_{R,ef}=10\,222\) psi.

### 5.3 Módulo 4 — Flexibles

**Entrada:** \(W_{18}\) (del mód. 1 o manual), \(R\), \(S_o\), \(p_0\), \(p_t\),
\(M_{R,ef}\) (del mód. 2 o manual), calidad de drenaje y % de saturación →
\(m_2,m_3\) (tabla AASHTO, con alternativa boliviana), \(E_{CA},E_B,E_{SB}\)
(directos o por CBR), \(a_i\) (calculados o manuales), etapas (1 o 2),
tabla de mínimos (AASHTO pulg o métrica cm).

**Cálculo:**

1. \(Z_R=-\Phi^{-1}(R)\); si etapas \(=2\), \(R_{etapa}=R^{1/2}\).
2. Resolver \(SN\) por bisección en la ecuación:

   \[
   0 = Z_R S_o + 9{,}36\log(SN+1) - 0{,}20
   + \frac{\log\left(\frac{\Delta PSI}{4{,}2-1{,}5}\right)}{0{,}40+\frac{1094}{(SN+1)^{5{,}19}}}
   + 2{,}32\log M_R - 8{,}07 - \log W_{18}
   \]

3. \(SN_1\) con \(M_R=E_B\); \(SN_2\) con \(M_R=E_{SB}\); \(SN_3=SN\).
4. Espesores: \(D_1=SN_1/a_1\); \(D_2=(SN_2-SN_1^*)/(a_2m_2)\);
   \(D_3=(SN-SN_1^*-SN_2^*)/(a_3m_3)\); aplicar mínimos y redondear arriba a 0,5 cm.
5. Verificar \(SN_1^*+SN_2^*+SN_3^*\ge SN\).
6. Iteración \(SN\)↔LEF opcional (punto fijo).

Coeficientes (verificados en la wiki):

- \(a_1=0{,}17\ln E_{CA}-1{,}7754\)
- \(a_2=0{,}249\log E_B-0{,}977\)
- \(a_3=0{,}227\log E_{SB}-0{,}839\)
- \(E_B=9380\ln CBR-12960\) · \(E_{SB}=4326\ln CBR+241\)

**Validación:** práctico 3 → \(SN=3{,}1\); 13 / 15 / 10 cm (total 38 cm).

### 5.4 Módulo 6 — Clima y vida útil

**Entrada:** hinchamiento (\(V_R\), \(P_S\), \(\theta\)); helada opcional
(\(P_F\), \(\Delta PSI_{max}\), \(\phi\), coeficiente \(0{,}02\) editable);
\(\Delta PSI\) total; \(SN\) adoptado; \(W(t)\) del módulo 1.

**Cálculo:**

- \(\Delta PSI_{SW}=0{,}00335\,V_R\,P_S(1-e^{-\theta t})\)
- \(\Delta PSI_{FH}=0{,}01\,P_F\,\Delta PSI_{max}(1-e^{-0{,}02\phi t})\)
- \(\Delta PSI_{TR}=\Delta PSI-\Delta PSI_{SW}-\Delta PSI_{FH}\)
- \(W_{adm}\) con la ecuación 5.3 al \(SN\) y \(M_R\) dados.
- Invertir \(W(t)\) por bisección; iterar \(t\) hasta \(|t_{sup}-t_{calc}|<1\) año,
  promediando. Si \(\Delta PSI_{TR}\le0\): error explicativo.

**Validación:** práctico 3 → \(\Delta PSI_{SW}(15)=0{,}312\); \(W=859\,000\);
\(T=14{,}8\) años.

## 6. Datos LEF

- Fuente: `fuentes_texto/lefs_docling.md` (18 tablas, decimales perdidos).
- Se reconstruyen **solo D.1–D.9** (flexibles): simple/tándem/trídem × \(p_t\) 2,0/2,5/3,0.
- `scripts/parse_lef_docling.py` parsea el `.md`, prueba las posiciones de
  punto decimal por celda y elige la que cumpla monotonicidad creciente con la
  carga, continuidad entre filas y el ancla 18 kip = 1,00 (ejes simples).
- Las celdas con ambigüedad se marcan `estado: dudoso` y se revisan contra la
  imagen de la página.
- Carga con validación: forma correcta, monotonicidad y ancla; rechaza si falla.
- Contraste adicional con los valores ya usados en el práctico 3 (2/4/8/14/22 kip;
  tándem 36; trídem 50).

## 7. Validación y tests

`pytest` sin red. Valores dorados:

| Resultado | Esperado | Tolerancia |
|---|---|---|
| \(M_{R,ef}\) | 10.222 psi | ±0,5 % |
| \(W_{15}\) | 890.521 ESAL | ±0,5 % |
| \(SN\) | 3,1 | ±0,02 |
| Espesores | 13 / 15 / 10 cm | exacto tras redondeo |
| Período con hinchamiento | 14,8 años | ±0,1 |

Segundo caso: apéndice H (\(M_{R,ef}\approx5\,700\) psi; \(SN\approx5{,}55\);
8 / 7 / 11,5 pulg) con tolerancia por origen en nomograma.

Tests de propiedades: LEF monótono con la carga; \(M_{R,ef}\) entre el mínimo y
el máximo mensual; verificación de espesores \(SN^*\ge SN\); bisección converge.

## 8. Interfaz y reporte

- Sidebar: Inicio, 1 Tránsito, 2 Subrasante, 4 Flexibles, 6 Clima, Validación,
  7 Marshall (deshabilitado).
- Cada página: Entrada → Resultados (tarjetas + tabla) → Procedimiento
  (desplegable con ecuaciones y valores intermedios).
- Estado en `st.session_state` (objeto `Proyecto`); aviso cuando un cambio
  desactualiza resultados aguas abajo.
- Guardar/cargar `.json`; exportar tablas a CSV.
- Reporte HTML autocontenido: portada, entradas, resultados, procedimiento,
  advertencias y sello de validación. CSS de impresión A4.

## 9. Manejo de errores

- Excepciones `DatosInvalidos` (bloqueante) y `NoConverge`.
- Advertencias no bloqueantes: \(R\) fuera de rango recomendado,
  \(E_{SB}/M_R>4\), mínimo constructivo gobierna, LEF fuera de rango de tabla,
  \(SN\) no convergió.

## 10. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Celdas LEF ambiguas | Revisión visual solo de las dudosas; test golden |
| Discrepancia de fuentes (tesis vs. avance 1) | Seguir la ruta ya verificada en la wiki |
| Circularidad SN↔LEF | Punto fijo acotado, opcional, con tabla de convergencia |
| Streamlit en Python 3.14 | venv con Python 3.13 (uv), probado |
| Helada sin fórmula confirmada | Coeficiente editable y marcado pendiente |

## 11. Orden de trabajo

1. Repo + venv + `pavimentos/unidades.py` + `lef.py` + `scripts/parse_lef_docling.py` → `data/lef.json`.
2. `resiliente.py` + test (10.222).
3. `trafico.py` + test (890.521).
4. `flexible.py` + test (SN 3,1; 13/15/10 cm).
5. `ambiental.py` + test (14,8 años).
6. `app.py` Streamlit + página de validación.
7. Reporte HTML + guardar/cargar.
8. Manual de usuario y memoria técnica (etapa posterior).
