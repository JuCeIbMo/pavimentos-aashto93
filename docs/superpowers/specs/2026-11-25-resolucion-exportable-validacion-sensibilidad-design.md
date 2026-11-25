# Diseño — Resolución integrada, exportación PDF/Excel, validación ampliada y sensibilidad

Fecha: 2026-11-25
Estado: en ejecución (el usuario pidió avanzar sin más preguntas)

## 1. Intención

Proyecto final de Carreteras II (consigna `PROYECTO DE CARRETERAS 2.pdf`). Según lo acordado
con el docente, el alcance es **solo pavimentos flexibles y sin Marshall** (módulos 1, 2, 4 y 6).
El objetivo es sacar la nota máxima. La app tiene que ser **una herramienta profesional y,
a la vez, didáctica**: que explique los conceptos, que sea intuitiva y que **toda resolución
se pueda exportar** (PDF y Excel) para guardarla o mostrarla en vivo.

## 2. Problemas encontrados en la base actual (hecha con DeepSeek)

- El motor `pavimentos/` está bien: reproduce el práctico 3, el Anexo V de la tesis y el
  Apéndice H de la guía.
- La interfaz **no conecta los módulos**: el módulo 4 tiene W18 y M_R fijos; el módulo de
  clima usa siempre el tránsito del práctico 3.
- "Guardar proyecto" guarda un archivo vacío: `Proyecto` nunca se llena.

## 3. Objetivos

1. Modelo único de entradas (`pavimentos/modelo.py`) y función pura `resolver(proyecto)`
   que calcula toda la cadena 1 → 2 → 4 → 6, con resultados intermedios, **decisiones**
   y **avisos**.
2. Validación con 4 ejercicios de fuentes distintas, guardados como proyectos completos más
   los valores esperados de la fuente:
   - Práctico 3 (cátedra).
   - Examen N° 1 (resolución oficial del docente, sin enunciado). Tránsito con
     "factor de camión conocido". La resolución tiene errores aritméticos en el tránsito:
     la fila 4 da 5,21 M cuando debería dar 1,90 M, y la suma de filas no coincide con
     el total. La app los muestra con respeto y valida el resto con el W18 que usó la fuente.
   - Apéndice H de la guía AASHTO 93 (M_R por quincenas, hinchamiento, a_i de figuras).
   - Anexo V de la tesis de Cabezas (2006).
3. Sensibilidad: curva de SN y espesores frente a una variable (R, So, ΔPSI, M_R, W18),
   más un gráfico tornado con variación de ±X % por variable.
4. Escenarios: hasta 3 variantes del proyecto actual, comparadas lado a lado.
5. Exportación:
   - **PDF** (memoria de cálculo) generado con **Typst** (paquete pip `typst`, sin LaTeX
     instalado). Lleva datos, procedimiento con ecuaciones, tablas, esquema de la estructura,
     decisiones, verificaciones y referencias.
   - **Excel** (`openpyxl`) con **fórmulas vivas**: tránsito, M_R, verificación de la
     ecuación AASHTO con el SN adoptado y espesores con redondeo, de modo que el docente
     pueda cambiar datos y ver cómo se recalcula.
6. Bibliografía: fuente debajo de cada ecuación, página "Referencias" y sección final del PDF.
7. Didáctica: `help` en cada dato de entrada (qué es, valores típicos) y un bloque
   "Concepto" por módulo.
8. Coeficiente de helada 0,02: **verificado** (avance 1, pág. 52, ec. G.8).

## 4. No-objetivos

- Pavimentos rígidos (módulos 3 y 5) y Marshall (módulo 7).
- Rediseño visual: se hace después, junto con el usuario. Ahora se reescriben las páginas
  sobre el modelo nuevo, conservando el tema actual.

## 5. Decisiones (del constructor)

| Tema | Decisión |
|---|---|
| Fuente de W18 en diseño | `calculado` (módulo 1) o `dato` (W18 conocido) |
| Fuente de M_R | `calculado` (módulo 2) o `dato` |
| Módulos de capa | E desde CBR (correlaciones de la tesis) o E directo |
| Coeficientes a_i | por correlación desde E, o `dato` (figuras AASHTO) |
| Tránsito por vehículo | ejes (LEF tabulados) o factor de camión conocido |
| M_R por período | desde CBR o M_R directo; los meses pueden ser fraccionarios (quincenas) |
| Adopción de SN | redondeo hacia arriba a 0,1 (configurable), como en el práctico y el Apéndice H |
| Redondeo de espesores | unidad (cm o pulg) y paso configurables |
| Espesores mínimos | tabla AASHTO según W18 (automática), personalizados o sin mínimos |
| Clima | opcional; si está activo, los espesores usan W admisible y ΔPSI remanente (como el práctico 3) |
| PDF | Typst; gráficos con matplotlib (PNG) |
| Comparación de validación | tolerancia relativa por valor; tabla fuente / app / diferencia % |

## 6. Archivos

- `pavimentos/modelo.py`: dataclasses de entrada, `to_dict` y `from_dict`.
- `pavimentos/resolver.py`: `resolver(proyecto) -> dict`.
- `pavimentos/sensibilidad.py`: barrido, tornado y escenarios.
- `pavimentos/validacion.py`: carga `data/validacion/*.json` y compara.
- `pavimentos/referencias.py`: bibliografía y fuente por ecuación.
- `pavimentos/exportar_pdf.py`, `pavimentos/exportar_excel.py`.
- `app/`: páginas reescritas sobre `st.session_state["proyecto"]` (un `ProyectoFlexible`).
- `tests/`: validación parametrizada, exportaciones y resolver.
