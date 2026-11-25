"""Modelo único de entradas de un proyecto de pavimento flexible.

Todo lo que el usuario carga vive acá. La interfaz, el resolver, el PDF, el Excel,
los escenarios y la validación leen y escriben este mismo objeto, así los módulos
quedan siempre conectados.

Unidades de entrada:
- CBR en %, M_R y módulos E en psi (la interfaz convierte kg/cm² → psi).
- Cargas por eje en toneladas o en kip (Transito.unidad_carga). Las toneladas se
  convierten a kip con el factor exacto 1 t = 2,20462 kip.
- Espesores mínimos y redondeo en la unidad elegida (cm o pulg).
"""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field, fields

KIP_POR_T = 2.20462              # 1 t = 1000 kg = 2204,62 lb = 2,20462 kip

# Distribución por carril recomendada por AASHTO 93 (Parte II, 2.1.3): carriles por sentido → (mín, máx)
FC_AASHTO = {1: (1.00, 1.00), 2: (0.80, 1.00), 3: (0.60, 0.80), 4: (0.50, 0.75)}
FD_AASHTO = (0.30, 0.70)         # distribución direccional (normalmente 0,5)


@dataclass
class Vehiculo:
    nombre: str = "Vehículo"
    tpda: float = 0.0                 # vehículos/día (ambos sentidos)
    r: float = 0.0                    # tasa de crecimiento anual (fracción, 0.03 = 3 %)
    pesado: bool = False
    ejes: list = field(default_factory=list)   # [["simple"|"tandem"|"tridem", carga], ...] en Transito.unidad_carga
    factor_camion: float | None = None         # si se conoce, reemplaza a los ejes


@dataclass
class Transito:
    n: float = 15.0                   # período de diseño / vida útil de la etapa (años)
    fd: float = 0.5                   # distribución direccional
    fc: float = 1.0                   # distribución por carril
    carriles: int = 1                 # carriles por sentido (define el rango recomendado de Fc; 4 = 4 o más)
    pt: float = 2.0                   # serviciabilidad terminal usada para los LEF
    sn_lef: float = 3.0               # SN supuesto: columna de las tablas LEF (1 a 6)
    unidad_carga: str = "t"           # unidad de las cargas por eje: "t" | "kip"
    vehiculos: list = field(default_factory=list)


@dataclass
class Periodo:
    nombre: str = "Período"
    meses: float = 1.0                # admite fracciones (quincenas = 0.5)
    cbr: float | None = None          # si se da CBR, M_R se obtiene por correlación
    mr: float | None = None           # M_R directo (psi); tiene prioridad sobre CBR


MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]


@dataclass
class Subrasante:
    # un período por mes (la interfaz trabaja con los 12 meses; el motor acepta cualquier
    # partición del año que sume 12 meses, como la de algunos ejercicios resueltos)
    periodos: list = field(default_factory=lambda: [Periodo(nombre=m) for m in MESES])
    dato: str = "cbr"                 # qué se carga por mes en la interfaz: "cbr" | "mr"


@dataclass
class Capa:
    """Material de una capa. Se puede dar E directo o CBR (base/subbase) y a directo."""
    e_psi: float | None = None
    cbr: float | None = None
    a: float | None = None            # coeficiente estructural dado (figuras AASHTO)
    m: float = 1.0                    # coeficiente de drenaje (no aplica a la carpeta)


@dataclass
class Diseno:
    r_pct: float = 85.0
    etapas: int = 1
    so: float = 0.45
    p0: float = 4.2
    pt: float = 2.5
    fuente_w18: str = "calculado"     # "calculado" (módulo 1) | "dato"
    w18_dato: float | None = None
    fuente_mr: str = "calculado"      # "calculado" (módulo 2) | "dato"
    mr_dato: float | None = None
    carpeta: Capa = field(default_factory=lambda: Capa(e_psi=400_000.0))
    base: Capa = field(default_factory=lambda: Capa(cbr=80.0))
    subbase: Capa = field(default_factory=lambda: Capa(cbr=30.0))
    paso_sn: float = 0.1              # SN adoptado = redondeo hacia arriba a este paso (0 = no)
    unidad: str = "cm"                # unidad de espesores: "cm" | "pulg"
    paso_espesor: float = 0.5         # redondeo hacia arriba de los espesores
    minimos: str = "aashto"           # "aashto" (según W18) | "personalizado" | "ninguno"
    min_carpeta: float = 0.0          # en la unidad elegida (solo si minimos == "personalizado")
    min_base: float = 0.0
    min_subbase: float = 0.0
    # Selecciones de los atajos de la interfaz (solo para mostrarlas; el cálculo usa r_pct, so, pt y m)
    tipo_via: str | None = None       # "autopista" | "arteria" | "colectora" | "local"
    zona: str | None = None           # "urbana" | "rural"
    drenaje_calidad: int | None = None      # fila de la tabla de drenaje (0 = excelente … 4 = muy mala)
    drenaje_saturacion: int | None = None   # columna (% del tiempo cerca de la saturación)


@dataclass
class Helada:
    pf: float = 50.0                  # probabilidad de levantamiento (%)
    dpsi_max: float = 1.0             # pérdida máxima de serviciabilidad
    phi: float = 2.0                  # tasa de levantamiento (mm/día)


@dataclass
class Clima:
    activo: bool = False
    hinchamiento: bool = True
    vr: float = 0.0                   # levantamiento vertical potencial (pulg)
    ps: float = 0.0                   # probabilidad de hinchamiento (%)
    theta: float = 0.1                # tasa de hinchamiento
    helada: Helada | None = None


@dataclass
class ProyectoFlexible:
    nombre: str = "Proyecto sin título"
    autor: str = ""
    ubicacion: str = ""
    descripcion: str = ""
    transito: Transito = field(default_factory=Transito)
    subrasante: Subrasante = field(default_factory=Subrasante)
    diseno: Diseno = field(default_factory=Diseno)
    clima: Clima = field(default_factory=Clima)

    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def copia(self) -> "ProyectoFlexible":
        return copy.deepcopy(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ProyectoFlexible":
        d = dict(d)
        tr = dict(d.get("transito") or {})
        tr["vehiculos"] = [_build(Vehiculo, v) for v in tr.get("vehiculos", [])]
        sub = dict(d.get("subrasante") or {})
        sub["periodos"] = [_build(Periodo, p) for p in sub.get("periodos", [])]
        di = dict(d.get("diseno") or {})
        for k in ("carpeta", "base", "subbase"):
            if isinstance(di.get(k), dict):
                di[k] = _build(Capa, di[k])
        cl = dict(d.get("clima") or {})
        if isinstance(cl.get("helada"), dict):
            cl["helada"] = _build(Helada, cl["helada"])
        return cls(
            nombre=d.get("nombre", "Proyecto sin título"),
            autor=d.get("autor", ""),
            ubicacion=d.get("ubicacion", ""),
            descripcion=d.get("descripcion", ""),
            transito=_build(Transito, tr),
            subrasante=_build(Subrasante, sub),
            diseno=_build(Diseno, di),
            clima=_build(Clima, cl),
        )

    @classmethod
    def from_json(cls, texto: str) -> "ProyectoFlexible":
        return cls.from_dict(json.loads(texto))


def _build(klass, d: dict):
    """Construye una dataclass ignorando claves desconocidas (archivos viejos o futuros)."""
    validas = {f.name for f in fields(klass)}
    return klass(**{k: v for k, v in d.items() if k in validas})
