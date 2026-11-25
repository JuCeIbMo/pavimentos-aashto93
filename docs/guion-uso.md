# Guion: explicación de uso de la app, con datos para ir cargando

Los valores son los del proyecto de ejemplo de la app (los mismos que trae al abrirse) y los resultados son los que devuelve el motor con esos datos.
Para la demostración en vivo:

- **Opción completa:** Inicio → "Proyecto en blanco" y cargar todo lo de abajo.
- **Opción rápida (recomendada si hay poco tiempo):** arrancar con el proyecto de ejemplo ya cargado, cargar en vivo 2 o 3 filas o valores, y cambiar un dato para mostrar que todo se recalcula.

En cada módulo: **Entra** = qué recibe de otro módulo · **Ingresás** = lo que tipeás · **Devuelve** = lo que calcula · **Decís** = qué explicar.

---

## 1. Inicio

**Ingresás** (tarjeta "Datos del proyecto"):

| Campo | Valor |
|---|---|
| Nombre del proyecto | Diseño de pavimento flexible – Tramo de ejemplo |
| Autor / proyectista | (tu nombre) |
| Ubicación | (la del enunciado) |

**Decís:** "Estos datos salen en la portada de la memoria de cálculo. La app resuelve los módulos 1, 2, 4 y 6 de la consigna y están conectados."

---

## 2. Módulo 1 · Tránsito

**Entra:** nada, es el primer módulo.

### Ingresás: parámetros

| Campo | Valor | Qué es |
|---|---|---|
| Período n (años) | 15 | Vida de diseño |
| Reparto por sentido → Fd | Parejo en ambos → 0,50 | Distribución direccional |
| Carriles por sentido → Fc | 1 → 1,00 | Factor de carril (tabla AASHTO) |
| pt de las tablas LEF | 2,0 | Serviciabilidad final con que se leen las tablas |
| SN supuesto (LEF) | 3 | SN con que se leen las tablas (se verifica al final) |
| Cargas en | toneladas | 1 t = 2,2046 kip |

### Ingresás: composición vehicular

Con "Agregar vehículo" elegís la disposición de ejes; después escribís las cargas por eje (t), el TPDA y la tasa de crecimiento.

| Vehículo | Ejes (tipo · carga en t) | TPDA | Tasa % |
|---|---|---|---|
| Automóvil | simple 1 · simple 1 | 250 | 3 |
| Camioneta | simple 1 · simple 2 | 65 | 3 |
| Minibús | simple 1 · simple 2 | 315 | 3 |
| Bus 12-21 | simple 1 · simple 4 | 1 | 3 |
| Bus 21-35 | simple 2 · simple 11 | 25 | 5 |
| Bus 35+ | simple 7 · tándem 18 | 35 | 4 |
| Camión mediano | simple 7 · simple 11 | 32 | 2 |
| Camión grande 2 ejes | simple 7 · trídem 25 | 16 | 2 |
| Camión grande 3 ejes | simple 7 · simple 7 · tándem 18 | 8 | 1 |
| Semirremolque | simple 7 · trídem 25 · tándem 18 | 2 | 1 |
| Camión con remolque | simple 7 · simple 11 · trídem 25 · tándem 18 | 1 | 1 |
| Otros | simple 1 · simple 4 | 4 | 3 |

### Devuelve

Por cada eje: carga en kip y su **LEF**, interpolado de las tablas AASHTO. Ejemplo para mostrar, el Bus 35+:

- simple 7 t = 15,43 kip → LEF = 0,5395
- tándem 18 t = 39,68 kip → LEF = 2,0835
- **Factor camión** = 0,5395 + 2,0835 = **2,6230**

Por cada vehículo, la tabla de resultados:

| Vehículo | Factor camión | G (crecimiento) | ESAL año 1 | W en 15 años |
|---|---|---|---|---|
| Automóvil | 0,0008 | 18,60 | 35 | 652 |
| Camioneta | 0,0042 | 18,60 | 50 | 932 |
| Minibús | 0,0042 | 18,60 | 243 | 4.518 |
| Bus 12-21 | 0,0585 | 18,60 | 11 | 199 |
| Bus 21-35 | 3,6157 | 21,58 | 16.497 | 355.972 |
| Bus 35+ | 2,6230 | 20,02 | 16.754 | 335.477 |
| Camión mediano | 4,1513 | 17,29 | 24.244 | 419.258 |
| Camión grande 2 ejes | 2,3501 | 17,29 | 6.862 | 118.671 |
| Camión grande 3 ejes | 3,1624 | 16,10 | 4.617 | 74.322 |
| Semirremolque | 4,4335 | 16,10 | 1.618 | 26.049 |
| Camión con remolque | 8,0454 | 16,10 | 1.468 | 23.635 |
| Otros | 0,0585 | 18,60 | 43 | 794 |

Indicadores finales:

- **W18 de diseño = 1.360.479 ESAL** (carril de diseño, 15 años)
- ESAL del primer año = 72.442
- TPDA total = 754 veh/día (120 pesados, 15,9 %)
- Fd × Fc = 0,5 × 1

### Decís

"Cada eje se convierte a kip y se busca su factor de equivalencia en las tablas AASHTO. La suma de los LEF de un vehículo es su factor camión.
ESAL del primer año = TPDA × 365 × factor camión × Fd × Fc, y se multiplica por el factor de crecimiento G = ((1+r)ⁿ − 1)/r.
Los autos casi no aportan: el camión mediano, con solo 32 por día, aporta el 30 % del W18. El daño depende de la carga por eje, no de la cantidad de vehículos."

---

## 3. Módulo 2 · Subrasante

**Entra:** nada de otro módulo.

### Ingresás

"Dato de cada mes" → **CBR (%)**. Un valor por mes:

| Mes | CBR % |
|---|---|
| Enero, Febrero, Marzo | 4,7 |
| Abril | 6,7 |
| Mayo | 8,4 |
| Junio a Octubre | 13,1 |
| Noviembre, Diciembre | 8,4 |

Tip: con la flechita ↓ copiás el valor al mes siguiente.

### Devuelve

| Mes | CBR | MR (psi) | Correlación | uf |
|---|---|---|---|---|
| Ene–Mar | 4,7 | 7.050 | 1500·CBR | 0,1393 |
| Abr | 6,7 | 10.050 | 1500·CBR | 0,0612 |
| May, Nov, Dic | 8,4 | 11.965 | 3000·CBR^0,65 | 0,0408 |
| Jun–Oct | 13,1 | 15.972 | 3000·CBR^0,65 | 0,0209 |

- Σuf = 0,7063 → **ūf = 0,0589**
- **MR efectivo = 10.222 psi** (≈ 719 kg/cm²)
- Promedio aritmético = 12.246 psi (no se usa)

### Decís

"Con CBR < 7,2 se usa MR = 1500·CBR, y con CBR mayor, 3000·CBR^0,65. Cada mes tiene un daño relativo uf = 1,18·10⁸·MR^−2,32.
El MR efectivo es el que produce el mismo daño anual que la variación real. Da 10.222, un 16,5 % menos que el promedio, porque enero a marzo, con suelo saturado, dañan casi 7 veces más que los meses secos."

---

## 4. Módulo 4 · Diseño flexible

**Entra:** W18 = 1.360.479 del módulo 1 y MR = 10.222 psi del módulo 2 (selectores "Del módulo 1" y "Del módulo 2").

### Ingresás: confiabilidad y serviciabilidad

| Campo | Valor |
|---|---|
| Tipo de vía / Zona | Otro (a mano) / Rural |
| R (%) | 85 |
| Errores en el tránsito → So | Con errores → 0,49 |
| p0 inicial | 4,2 |
| pt terminal | 2,0 → ΔPSI = 2,20 |
| Etapas de construcción | 2 |

### Ingresás: materiales

| Capa | Dato | Drenaje m |
|---|---|---|
| Carpeta asfáltica | E = 29.881 kg/cm² (= 425.000 psi) | — |
| Base granular | CBR = 80 % | m₂ = 1,00 |
| Subbase granular | CBR = 40 % | m₃ = 1,00 |

### Ingresás: criterios de redondeo y mínimos

| Campo | Valor |
|---|---|
| Unidad de espesores | centímetros |
| Redondear espesores a | 0,5 cm |
| Redondear SN a | 0,1 |
| Espesores mínimos | Personalizados: carpeta 7,5 · base 15 · subbase 10 cm |

### Devuelve

- R por etapa = R^(1/2) = **92,2 %** → ZR = −1,418
- **SN requerido = 3,254** → se adopta **SN = 3,30**
- Coeficientes: a₁ = 0,428 · a₂ = 0,131 · a₃ = 0,117

| Capa | SN req. | D calculado | D adoptado | Mínimo |
|---|---|---|---|---|
| Carpeta | 2,260 | 13,42 cm | **13,5 cm** | 7,5 |
| Base | 2,782 | 9,87 cm | **15,0 cm** | 15 (gobierna el mínimo) |
| Subbase | 3,300 | 5,52 cm | **10,0 cm** | 10 (gobierna el mínimo) |

- **Espesor total = 38,5 cm**, SN aportado = 3,505
- Verificaciones, todas cumplen:
  - SN₁* 2,274 ≥ 2,260
  - SN₁* + SN₂* 3,047 ≥ 2,782
  - SN total 3,505 ≥ 3,300
- Verificación de los LEF: SN de diseño 3,3 contra SN supuesto 3 → diferencia < 0,5, no hace falta recalcular.

### Decís

"Con 2 etapas, cada una tiene que cumplir R^(1/2) para que el conjunto cumpla el 85 %.
La ecuación AASHTO no se puede despejar para el SN, así que se resuelve por bisección: da 3,254 y se adopta 3,30.
Los espesores se calculan de arriba hacia abajo: la carpeta protege a la base, base más carpeta protegen a la subbase, y todo protege a la subrasante.
En base y subbase gobierna el espesor mínimo, no el cálculo."

Nota: con Clima activado, los espesores usan W = 1.273.917 y ΔPSI = 1,888 (ver módulo 6).

---

## 5. Módulo 6 · Clima

**Entra:** el SN y la estructura del módulo 4, el W18 y su crecimiento del módulo 1, y el MR del módulo 2.

### Ingresás

| Campo | Valor |
|---|---|
| Considerar efectos ambientales | Activado |
| Hinchamiento → Incluir | Sí |
| VR (pulg) | 2,0 |
| PS (%) | 60 |
| θ | 0,10 |
| Levantamiento por helada | No |

### Devuelve

Iteración (tabla):

| t supuesto | ΔPSI SW | ΔPSI TR | W admisible | t calculado | \|Δt\| |
|---|---|---|---|---|---|
| 15 | 0,312 | 1,888 | 1.273.917 | 14,23 | 0,77 < 1 ✓ |

- **Período de desempeño = 14,6 años** (promedio de 15 y 14,23), objetivo 15
- ΔPSI ambiental = 0,312 · ΔPSI para el tránsito = 1,888
- W admisible = 1.273.917 ESAL

### Decís

"La arcilla expansiva le quita 0,312 de serviciabilidad al pavimento sin que pase ningún camión, así que al tránsito le queda 2,2 − 0,312 = 1,888.
Con ese margen la estructura admite 1.273.917 ESAL, que se acumulan a los 14,2 años. Como difiere menos de 1 año del supuesto, converge: hay que prever un recapado a los 14,6 años o aumentar el SN."

---

## 6. Sensibilidad

**Entra:** el proyecto completo. No lo modifica: trabaja sobre copias.

### Ingresás y devuelve

| Pestaña | Ingresás | Devuelve |
|---|---|---|
| Curva de una variable | Variable: MR; Desde 5.000, Hasta 20.000 | SN y espesores a lo largo del rango |
| Tornado | Variación ±10 % (deslizador); medir sobre SN requerido | Variables ordenadas de la que más pesa a la que menos |
| Escenarios | Escenario 1 "Tránsito alto": W18 × 1,5 · Escenario 2 "Subrasante pobre": MR = 7.050 | SN y espesores de cada alternativa, lado a lado |

### Decís

"El tornado muestra qué dato conviene medir con más cuidado. Los escenarios permiten comparar alternativas sin tocar el proyecto."

(Los resultados exactos de esta pestaña los leés en pantalla, dependen del rango que elijas.)

---

## 7. Validación

**Ingresás:** nada. Abrís un ejercicio con la flechita.

**Devuelve:**
- 4 ejercicios aprobados de 4: práctico 3, examen 1, Apéndice H de la guía AASHTO y Anexo V de Cabezas (2006)
- **45 de 45** valores dentro de la tolerancia
- Mayor diferencia: 4,17 %

**Decís:** "Cada ejercicio se resuelve con el programa y se compara valor por valor con la fuente. Con 'Cargar este ejercicio en la app' se puede recorrer cualquiera módulo por módulo."

---

## 8. Exportación

**Ingresás:** botones "Memoria PDF" y "Excel" de la barra superior (se habilitan con el diseño completo).

**Devuelve:**
- **PDF:** memoria de cálculo con datos, ecuaciones, resultados intermedios y decisiones.
- **Excel:** libro con fórmulas vivas; si cambiás un dato, recalcula (el SN se resuelve por bisección en celdas).
- "Guardar" descarga el proyecto como `.json` y "Abrir" lo vuelve a cargar.

---

## Demostración de que todo está conectado (30 s)

1. En Tránsito, cambiá el TPDA del **Camión mediano** de 32 a **64**.
2. Mirá la barra superior: el W18 y el SN se recalculan al instante.
3. Andá a Diseño y mostrá que cambiaron los espesores. Después volvé a poner 32.

---

## Preguntas probables

- **¿Por qué el MR efectivo y no el promedio?** Porque el daño no es lineal: los meses de MR bajo dañan mucho más, y el promedio sobreestima el soporte (12.246 contra 10.222 psi).
- **¿Cómo se obtiene el SN si no se puede despejar?** Por bisección: se prueban valores partiendo el intervalo por la mitad hasta que el tránsito admisible iguala al W18.
- **¿Por qué ZR es negativo?** Porque el área de confiabilidad queda a la derecha; al ser negativo, ZR·So exige más SN y ese es el margen de seguridad.
- **¿Por qué se verifica el SN supuesto?** Porque los LEF dependen del SN. Si el SN de diseño difiere en más de 0,5 del supuesto, hay que releer las tablas.
- **¿Por qué base y subbase salen más gruesas que el cálculo?** Porque gobiernan los espesores mínimos constructivos.
