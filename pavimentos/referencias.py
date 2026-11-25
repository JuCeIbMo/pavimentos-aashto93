"""Bibliografía y fuente de cada ecuación implementada.

`REFERENCIAS` es la lista bibliográfica (formato APA). `ECUACIONES` asocia cada
ecuación del paquete con su expresión LaTeX, su fuente y una explicación breve; la
interfaz la muestra debajo de cada ecuación y el PDF la usa en la memoria de cálculo.
"""

REFERENCIAS = {
    "aashto93": "AASHTO (1993). *AASHTO Guide for Design of Pavement Structures*. American Association "
                "of State Highway and Transportation Officials, Washington D.C.",
    "aashto93_d": "AASHTO (1993). *Guide for Design of Pavement Structures*, Apéndice D: Factores de "
                  "equivalencia de carga (tablas D.1–D.9).",
    "aashto93_g": "AASHTO (1993). *Guide for Design of Pavement Structures*, Apéndice G: Tratamiento de "
                  "suelos expansivos y heladas.",
    "aashto93_h": "AASHTO (1993). *Guide for Design of Pavement Structures*, Apéndice H: Ejemplo de diseño "
                  "de pavimento flexible.",
    "cabezas2006": "Cabezas Ortiz, L. G. (2006). *Sistematización del diseño para pavimentos flexibles — "
                   "Empleo del método AASHTO '93* (Tesis de maestría). Universidad Autónoma Juan Misael "
                   "Saracho, Tarija.",
    "avance1": "Cátedra Carreteras II (2026). *Avance 1: Consideraciones de diseño — Pavimentos flexibles "
               "AASHTO 93* (apunte de clase). UAJMS.",
    "huang2004": "Huang, Y. H. (2004). *Pavement Analysis and Design* (2.ª ed.). Pearson Prentice Hall.",
}

ECUACIONES = {
    "crecimiento": {
        "latex": r"G = \dfrac{(1+r)^n - 1}{r}",
        "fuente": "AASHTO 93, Parte I, ap. D; avance 1",
        "ref": "aashto93",
        "explica": "Factor de crecimiento compuesto: cuántos «años equivalentes al primero» se acumulan en n años si el tránsito crece a la tasa r.",
    },
    "esal": {
        "latex": r"W_{18} = \sum_i TPDA_i \cdot F_{cam,i} \cdot 365 \cdot F_d \cdot F_c \cdot G_i",
        "fuente": "AASHTO 93, Parte II, sec. 2.1.2",
        "ref": "aashto93",
        "explica": "Ejes equivalentes de 18 kip (8,2 t) acumulados en el carril de diseño. F_cam es el factor camión: la suma de los LEF de sus ejes; F_d y F_c, las distribuciones por sentido y por carril.",
    },
    "lef": {
        "latex": r"F_{cam} = \sum_{ejes} LEF(\text{tipo}, \text{carga}, SN, p_t)",
        "fuente": "AASHTO 93, Apéndice D, tablas D.1–D.9",
        "ref": "aashto93_d",
        "explica": "El LEF dice cuántas pasadas del eje patrón de 18 kip producen el mismo daño que una pasada de ese eje. Crece aproximadamente con la 4.ª potencia de la carga.",
    },
    "mr_cbr": {
        "latex": r"M_R = 1500\,CBR \;\;(CBR<7{,}2\%) \qquad M_R = 3000\,CBR^{0{,}65} \;\;(7{,}2\%\le CBR\le 20\%)",
        "fuente": "AASHTO 93, Parte II, sec. 1.5; Cabezas (2006), §4.10",
        "ref": "aashto93",
        "explica": "Correlaciones empíricas para estimar el módulo resiliente cuando solo se tiene CBR.",
    },
    "danio": {
        "latex": r"u_f = 1{,}18\times10^{8}\, M_R^{-2{,}32}",
        "fuente": "AASHTO 93, Parte II, fig. 2.3",
        "ref": "aashto93",
        "explica": "Daño relativo de cada período: los meses en que la subrasante está débil (húmeda, en deshielo) consumen mucha más vida.",
    },
    "mr_ef": {
        "latex": r"\bar u_f = \dfrac{\sum u_{f,i}\, t_i}{12} \qquad M_{R,ef} = \left(\dfrac{\bar u_f}{1{,}18\times10^{8}}\right)^{-1/2{,}32}",
        "fuente": "AASHTO 93, Parte II, sec. 2.3.1",
        "ref": "aashto93",
        "explica": "El M_R efectivo es el módulo constante que produce el mismo daño anual que la variación estacional real.",
    },
    "zr": {
        "latex": r"R_{etapa} = R^{1/n} \qquad Z_R = \Phi^{-1}(1-R)",
        "fuente": "AASHTO 93, Parte I, cap. 4; Parte II, tabla 4.1",
        "ref": "aashto93",
        "explica": "Z_R es la desviación normal estándar para la confiabilidad elegida. Si se construye por etapas, cada etapa debe tener más confiabilidad para que el conjunto cumpla R.",
    },
    "aashto": {
        "latex": r"\log W_{18} = Z_R S_o + 9{,}36\log(SN+1) - 0{,}20 + \dfrac{\log\left(\dfrac{\Delta PSI}{4{,}2-1{,}5}\right)}{0{,}40 + \dfrac{1094}{(SN+1)^{5{,}19}}} + 2{,}32\log M_R - 8{,}07",
        "fuente": "AASHTO 93, Parte II, ec. 3.1 (fig. 3.1)",
        "ref": "aashto93",
        "explica": "Ecuación de diseño de pavimentos flexibles, obtenida del AASHO Road Test. Se resuelve para SN por bisección (equivale a leer el nomograma).",
    },
    "coef": {
        "latex": r"a_1 = 0{,}17\ln E_{CA} - 1{,}7754 \quad a_2 = 0{,}249\log E_B - 0{,}977 \quad a_3 = 0{,}227\log E_{SB} - 0{,}839",
        "fuente": "AASHTO 93, Parte II, figs. 2.5–2.7; Cabezas (2006), §4.11",
        "ref": "cabezas2006",
        "explica": "Coeficientes estructurales: cuánto SN aporta cada pulgada de material según su módulo.",
    },
    "e_cbr": {
        "latex": r"E_B = 9380\ln CBR - 12960 \qquad E_{SB} = 4326\ln CBR + 241",
        "fuente": "Cabezas (2006), §4.10.1",
        "ref": "cabezas2006",
        "explica": "Módulos de base y subbase granulares a partir del CBR del material.",
    },
    "sn": {
        "latex": r"SN = a_1 D_1 + a_2 m_2 D_2 + a_3 m_3 D_3",
        "fuente": "AASHTO 93, Parte II, ec. 3.2",
        "ref": "aashto93",
        "explica": "El número estructural se reparte entre las capas; m_i premia o castiga el drenaje de las capas granulares.",
    },
    "capas": {
        "latex": r"D_1 \ge \dfrac{SN_1}{a_1} \qquad D_2 \ge \dfrac{SN_2 - a_1 D_1^*}{a_2 m_2} \qquad D_3 \ge \dfrac{SN_3 - a_1 D_1^* - a_2 m_2 D_2^*}{a_3 m_3}",
        "fuente": "AASHTO 93, Parte II, fig. 3.2",
        "ref": "aashto93",
        "explica": "Diseño por capas: cada capa se dimensiona para proteger a la que está debajo, usando el módulo de esa capa inferior como si fuera la subrasante.",
    },
    "hinchamiento": {
        "latex": r"\Delta PSI_{SW} = 0{,}00335\, V_R\, P_S\,\left(1-e^{-\theta t}\right)",
        "fuente": "AASHTO 93, Apéndice G, ec. G.4",
        "ref": "aashto93_g",
        "explica": "Pérdida de serviciabilidad por suelos expansivos. Le «roba» ΔPSI al tránsito, por eso el pavimento dura menos.",
    },
    "helada": {
        "latex": r"\Delta PSI_{FH} = 0{,}01\, P_F\, \Delta PSI_{MAX}\,\left(1-e^{-0{,}02\,\phi\, t}\right)",
        "fuente": "AASHTO 93, Apéndice G, ec. G.8 (avance 1, pág. 52)",
        "ref": "aashto93_g",
        "explica": "Pérdida de serviciabilidad por levantamiento por congelamiento.",
    },
    "periodo": {
        "latex": r"\Delta PSI_{TR} = \Delta PSI - \Delta PSI_{SW} - \Delta PSI_{FH} \;\Rightarrow\; W_{adm} \;\Rightarrow\; t \;\text{ tal que }\; W(t)=W_{adm}",
        "fuente": "AASHTO 93, Parte II, sec. 3.1.4 y fig. 3.3",
        "ref": "aashto93",
        "explica": "Se itera el período de desempeño hasta que el período supuesto y el calculado difieran menos de 1 año.",
    },
}


def lista_referencias() -> list[tuple[str, str]]:
    return list(REFERENCIAS.items())
