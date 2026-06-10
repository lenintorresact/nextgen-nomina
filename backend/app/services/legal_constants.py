"""Constantes legales de nómina del Ecuador, indexadas por año.

Centraliza todos los parámetros que cambian cada año (SBU, tasas IESS, tabla del
Impuesto a la Renta, canasta básica, rebaja de gastos personales) para que la
actualización anual sea un cambio de datos y no de lógica.

Fuentes (verificar al iniciar cada año fiscal):
- SBU: Acuerdo Ministerial del Ministerio del Trabajo.
- Tasas IESS / fondos de reserva: IESS, sector privado régimen general.
- Tabla IR y rebaja de gastos personales: Resolución del SRI y LRTI.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# Cada tramo de la tabla del IR: (fracción básica, exceso hasta, impuesto de la
# fracción básica, % sobre el excedente). El último tramo usa float('inf').
IRBracket = Tuple[float, float, float, float]


@dataclass(frozen=True)
class LegalYear:
    """Conjunto de parámetros legales vigentes para un año fiscal."""
    sbu: float                                  # Salario Básico Unificado
    iess_employee: float                        # Aporte personal IESS
    iess_employer: float                        # Aporte patronal IESS (incl. IECE/SECAP)
    reserve_funds: float                        # Fondos de reserva (tras 1 año)
    canasta_basica: float                       # Canasta familiar básica (enero)
    ir_brackets: List[IRBracket]                # Tabla del Impuesto a la Renta
    gastos_rebate_rate: float                   # % de rebaja sobre gastos personales
    # Nº de canastas básicas tope para la rebaja, según nº de cargas familiares.
    canastas_by_cargas: Dict[int, int] = field(default_factory=dict)

    def canastas_for_cargas(self, cargas: int) -> int:
        """Nº de canastas tope para un nº de cargas (satura en el máximo definido)."""
        if not self.canastas_by_cargas:
            return 0
        max_cargas = max(self.canastas_by_cargas)
        return self.canastas_by_cargas[min(max(cargas, 0), max_cargas)]


# Tabla del IR 2026 — Resolución SRI NAC-DGERCGC25-00000043 (29-dic-2025).
_IR_BRACKETS_2026: List[IRBracket] = [
    (0.0, 12_208.0, 0.0, 0.00),
    (12_208.0, 15_549.0, 0.0, 0.05),
    (15_549.0, 20_188.0, 167.0, 0.10),
    (20_188.0, 26_700.0, 631.0, 0.12),
    (26_700.0, 35_136.0, 1_412.0, 0.15),
    (35_136.0, 46_575.0, 2_678.0, 0.20),
    (46_575.0, 62_005.0, 4_965.0, 0.25),
    (62_005.0, 82_679.0, 8_823.0, 0.30),
    (82_679.0, 109_956.0, 15_025.0, 0.35),
    (109_956.0, float("inf"), 24_572.0, 0.37),
]

# Tope de canastas básicas para la rebaja de gastos personales, por cargas.
# 0 cargas → 7 canastas; con cargas escala entre 9 y 20 (LRTI / Resolución SRI).
_CANASTAS_BY_CARGAS = {0: 7, 1: 9, 2: 11, 3: 14, 4: 17, 5: 20}

LEGAL_CONSTANTS: Dict[int, LegalYear] = {
    2024: LegalYear(
        sbu=460.0,
        iess_employee=0.0945,
        iess_employer=0.1215,
        reserve_funds=0.0833,
        canasta_basica=791.21,
        ir_brackets=_IR_BRACKETS_2026,  # placeholder histórico; no se usa para retención 2024
        gastos_rebate_rate=0.18,
        canastas_by_cargas=_CANASTAS_BY_CARGAS,
    ),
    2025: LegalYear(
        sbu=470.0,
        iess_employee=0.0945,
        iess_employer=0.1215,
        reserve_funds=0.0833,
        canasta_basica=805.00,
        ir_brackets=_IR_BRACKETS_2026,  # placeholder; reemplazar con tabla 2025 si se requiere
        gastos_rebate_rate=0.18,
        canastas_by_cargas=_CANASTAS_BY_CARGAS,
    ),
    2026: LegalYear(
        sbu=482.0,
        iess_employee=0.0945,
        iess_employer=0.1215,
        reserve_funds=0.0833,
        canasta_basica=821.80,
        ir_brackets=_IR_BRACKETS_2026,
        gastos_rebate_rate=0.18,
        canastas_by_cargas=_CANASTAS_BY_CARGAS,
    ),
}


def for_year(year: int) -> LegalYear:
    """Devuelve las constantes del año pedido.

    Si el año no existe, usa el año más cercano definido que sea <= year
    (los parámetros vigentes más recientes); si el año es anterior a todos,
    usa el más antiguo disponible. Así el motor nunca falla por un año futuro.
    """
    if year in LEGAL_CONSTANTS:
        return LEGAL_CONSTANTS[year]
    available = sorted(LEGAL_CONSTANTS)
    candidates = [y for y in available if y <= year]
    return LEGAL_CONSTANTS[candidates[-1] if candidates else available[0]]
