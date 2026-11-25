# Guion: explicación de uso de la app

Duración estimada: 8 a 10 minutos. Los números son los del proyecto de ejemplo que trae la app al abrirse.
**[Acción]** es lo que hacés en pantalla; el resto es lo que decís.

---

## 1. Inicio (1 min)

**[Acción]** Abrir https://carreteras-ii-julio-ibanez.doppel.lat/

> Esta es la aplicación de diseño de pavimentos flexibles por el método AASHTO 1993.
> Resuelve los módulos 1, 2, 4 y 6 de la consigna: tránsito, subrasante, diseño y clima.
> Los módulos están conectados: el W18 del módulo 1 y el MR del módulo 2 pasan solos al diseño.
> Cada vez que cambio un dato, todo se recalcula al instante.

**[Acción]** Señalar las cuatro tarjetas de "Flujo de cálculo".

> Acá se ve el estado de cada módulo y su resultado principal.
> En "Datos del proyecto" van el nombre, el autor y la ubicación, que salen en la portada del PDF.
> A la derecha se puede cargar un ejercicio resuelto o empezar un proyecto en blanco.

---

## 2. Módulo 1 · Tránsito (2 min)

**[Acción]** Ir a Tránsito.

> Primero los parámetros: período de diseño, factor de distribución direccional Fd y factor de carril Fc.
> Los selectores son atajos de las tablas AASHTO, pero el valor se puede corregir a mano.
> También el pt y el SN supuesto con que se leen las tablas LEF.

**[Acción]** Bajar a la tabla de composición vehicular.

> Cada fila es un vehículo con la forma del enunciado: carga y tipo de cada eje, TPDA y tasa de crecimiento.
> Las cargas se cargan en toneladas o en kip; la conversión es 1 t = 2,2046 kip.
> Debajo de cada eje aparece la carga en kip y su factor de equivalencia LEF, interpolado de las tablas AASHTO.
> El tilde verde indica que la fila está completa y entra al cálculo.

**[Acción]** Señalar los indicadores.

> Resultado: W18 de diseño = **1.360.479 ESAL** en el carril de diseño.
> En "Procedimiento y ecuaciones" está cada fórmula con su fuente.

---

## 3. Módulo 2 · Subrasante (1 min)

**[Acción]** Ir a Subrasante.

> Se carga el CBR o el MR de cada mes. Con el CBR, el MR se obtiene con las correlaciones AASHTO.
> Para cada mes se calcula el daño relativo uf, y con el daño promedio se obtiene el MR efectivo.

**[Acción]** Señalar los indicadores y el gráfico.

> MR efectivo = **10.222 psi**, menor que el promedio aritmético (12.246 psi).
> Se usa el efectivo porque los meses húmedos dañan mucho más: el gráfico muestra qué período daña más.

---

## 4. Módulo 4 · Diseño flexible (2 min)

**[Acción]** Ir a Diseño flexible.

> Toma el W18 del módulo 1 y el MR del módulo 2.
> Se define la confiabilidad R con la tabla 4.3, la desviación estándar So, y la serviciabilidad inicial y final.
> Con eso se resuelve la ecuación AASHTO por bisección, porque el SN no se puede despejar.

> SN requerido = **3,254**; se adopta **3,30**.

**[Acción]** Bajar a materiales y espesores.

> Los coeficientes estructurales a1, a2 y a3 salen de las propiedades de cada material.
> Los coeficientes de drenaje m salen de las tablas 4.12 y 4.13.
> Los espesores se calculan capa por capa con los mínimos constructivos, y se verifica que cada capa proteja a la de abajo.

> Resultado: carpeta **13,5 cm**, base **15 cm** y subbase **10 cm**, con un total de 38,5 cm. Las tres verificaciones cumplen.

---

## 5. Módulo 6 · Clima (1 min)

**[Acción]** Ir a Clima. Si el enunciado no habla de suelo expansivo ni de helada, mostrar que está desactivado y pasar al siguiente punto.

> Si la subrasante es expansiva o se congela, la serviciabilidad se pierde aunque no pase tránsito.
> El método es iterativo: se supone un período, se calcula la pérdida ambiental, se ve cuánto tránsito admite la estructura y se repite hasta que la diferencia es menor a un año.
> En el ejemplo, el período de desempeño da **14,6 años**: a esa edad hace falta una rehabilitación.

---

## 6. Sensibilidad (1 min)

**[Acción]** Ir a Sensibilidad → pestaña "Tornado".

> El diagrama tornado varía cada dato ±10 % y ordena cuál pesa más sobre el SN.
> Sirve para saber qué dato conviene medir con más cuidado.

**[Acción]** Pestaña "Escenarios".

> También se pueden comparar alternativas, por ejemplo más tránsito o una subrasante más pobre, y ver cómo cambian los espesores.

---

## 7. Validación (1 min)

**[Acción]** Ir a Validación.

> Para comprobar que el programa calcula bien, se resolvieron 4 ejercicios de fuentes independientes:
> el práctico 3 de la cátedra, el examen 1, el ejemplo del Apéndice H de la guía AASHTO y el Anexo V de la tesis de Cabezas.
> Se compararon 45 valores intermedios y finales, y los 45 están dentro de la tolerancia.

**[Acción]** Abrir el práctico 3 y mostrar la tabla fuente / app / diferencia.

---

## 8. Exportación (30 s)

**[Acción]** Tocar "Memoria PDF" y después "Excel".

> Al final se descarga la memoria de cálculo en PDF, con cada dato, ecuación y decisión,
> y el libro Excel con las fórmulas vivas: si se cambia un dato en el Excel, se recalcula.
> El proyecto se guarda y se abre como archivo con "Guardar" y "Abrir".

---

## Preguntas probables

- **¿Por qué el MR efectivo y no el promedio?** Porque el daño no es lineal: los meses de MR bajo dañan mucho más, y el promedio sobreestima el soporte.
- **¿Cómo se obtiene el SN si no se puede despejar?** Por bisección: se prueban valores de SN partiendo el intervalo por la mitad hasta que el tránsito admisible iguala al W18.
- **¿Por qué ZR es negativo?** Porque el área de confiabilidad R queda a la derecha. Al ser negativo, el término ZR·So exige más SN: ese es el margen de seguridad.
- **¿Qué pasa si cambio un dato del tránsito?** Se recalcula todo en cadena: W18 → SN → espesores → clima.
