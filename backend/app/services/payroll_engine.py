from datetime import datetime, date
from typing import List, Dict, Optional
from ..models.schemas import Employee, PayrollEvent, EventType, Region, SettlementCause
from . import legal_constants
from .legal_constants import LegalYear

# Mes de pago del décimo cuarto sueldo según región:
# Costa/Insular se paga hasta el 15 de marzo; Sierra/Amazonía hasta el 15 de agosto.
FOURTEENTH_PAYOUT_MONTH = {
    Region.COSTA: 3,
    Region.INSULAR: 3,
    Region.SIERRA: 8,
    Region.AMAZONIA: 8,
}

# Mes de inicio del ciclo de acumulación del décimo cuarto, por región.
FOURTEENTH_CYCLE_START_MONTH = {
    Region.COSTA: 3,
    Region.INSULAR: 3,
    Region.SIERRA: 8,
    Region.AMAZONIA: 8,
}

# Divisor para el valor de la hora (8 h x 30 días) y recargos de horas extras.
HOURLY_DIVISOR = 240
SUPPLEMENTARY_SURCHARGE = 1.5   # horas suplementarias: +50%
EXTRAORDINARY_SURCHARGE = 2.0   # horas extraordinarias: +100%

# Tope de la multa disciplinaria: 10% de la remuneración (Art. 44 Código del Trabajo).
MULTA_CAP_RATE = 0.10

# Tipos de novedad que constituyen ingresos gravables a monto fijo.
_FLAT_EARNING_TYPES = (
    EventType.OVERTIME_50, EventType.OVERTIME_100,
    EventType.COMMISSION, EventType.BONUS,
)
# Descuentos a monto fijo (se categorizan por su etiqueta).
_FLAT_DEDUCTION_TYPES = (
    EventType.DEDUCTION, EventType.PRESTAMO_QUIROGRAFARIO,
    EventType.PRESTAMO_HIPOTECARIO, EventType.ANTICIPO,
)


def _value_per_hour(salary: float) -> float:
    """Valor de la hora ordinaria: sueldo mensual / 240."""
    return salary / HOURLY_DIVISOR


def _as_date(value) -> date:
    """Normaliza datetime/date (tz-aware o naive) a un date puro."""
    if isinstance(value, datetime):
        return value.date()
    return value


def _thirteenth_cycle_start(t: date) -> date:
    """Inicio del ciclo del décimo tercero (1 de diciembre) vigente a la fecha t."""
    year = t.year if t.month == 12 else t.year - 1
    return date(year, 12, 1)


def _fourteenth_cycle_start(t: date, region: Region) -> date:
    """Inicio del ciclo del décimo cuarto a la fecha t, según región."""
    start_month = FOURTEENTH_CYCLE_START_MONTH.get(region, 8)
    year = t.year if t.month >= start_month else t.year - 1
    return date(year, start_month, 1)


def _last_anniversary(start: date, t: date) -> date:
    """Último aniversario de la fecha de ingreso en o antes de t."""
    try:
        this_year = start.replace(year=t.year)
    except ValueError:  # 29-feb en año no bisiesto
        this_year = start.replace(year=t.year, day=28)
    if this_year <= t:
        return this_year
    try:
        return start.replace(year=t.year - 1)
    except ValueError:
        return start.replace(year=t.year - 1, day=28)


def _prorated_days(cycle_start: date, hire: date, termination: date) -> int:
    """Días acumulados en un ciclo: desde max(inicio de ciclo, ingreso) hasta la salida."""
    effective_start = max(cycle_start, hire)
    return max(0, (termination - effective_start).days)


class PayrollEngine:
    @staticmethod
    def calculate_thirteenth(monthly_earnings: float) -> float:
        return monthly_earnings / 12

    @staticmethod
    def calculate_fourteenth(constants: LegalYear) -> float:
        # Provisión mensual del décimo cuarto: SBU / 12.
        # El monto es el mismo en todas las regiones; lo que cambia por región
        # es el mes de pago del acumulado (ver fourteenth_payout_month).
        return constants.sbu / 12

    @staticmethod
    def fourteenth_payout_month(region: Region) -> int:
        """Mes (1-12) en que se paga el acumulado del décimo cuarto según región."""
        return FOURTEENTH_PAYOUT_MONTH.get(region, 8)

    @staticmethod
    def calculate_iess_employee(taxable_earnings: float, constants: LegalYear) -> float:
        return taxable_earnings * constants.iess_employee

    @staticmethod
    def calculate_iess_employer(taxable_earnings: float, constants: LegalYear) -> float:
        return taxable_earnings * constants.iess_employer

    @staticmethod
    def calculate_reserve_funds(taxable_earnings: float, years_of_service: float,
                                constants: LegalYear) -> float:
        if years_of_service >= 1.0:
            return taxable_earnings * constants.reserve_funds
        return 0.0

    @staticmethod
    def calculate_vacations(taxable_earnings: float) -> float:
        return taxable_earnings / 24

    # --- Impuesto a la Renta ---------------------------------------------

    @staticmethod
    def calculate_ir_tax(annual_base: float, constants: LegalYear) -> float:
        """Impuesto a la Renta anual para una base imponible, según la tabla del año."""
        if annual_base <= 0:
            return 0.0
        for fraccion_basica, exceso_hasta, impuesto_fb, pct in constants.ir_brackets:
            if annual_base <= exceso_hasta:
                return impuesto_fb + (annual_base - fraccion_basica) * pct
        # Salvaguarda: si ningún tramo aplica, usar el último.
        fraccion_basica, _, impuesto_fb, pct = constants.ir_brackets[-1]
        return impuesto_fb + (annual_base - fraccion_basica) * pct

    @staticmethod
    def calculate_personal_expenses_rebate(gastos: float, cargas: int,
                                           constants: LegalYear,
                                           catastrophic: bool = False) -> float:
        """Rebaja por gastos personales: % sobre el menor entre los gastos
        declarados y el tope de N canastas básicas (según cargas familiares).

        Si `catastrophic` (carga con enfermedad catastrófica/rara/huérfana), el
        tope es de 100 canastas en lugar de la escala por nº de cargas.
        """
        if gastos <= 0:
            return 0.0
        canastas = constants.canastas_catastrophic if catastrophic \
            else constants.canastas_for_cargas(cargas)
        tope = canastas * constants.canasta_basica
        return constants.gastos_rebate_rate * min(gastos, tope)

    @classmethod
    def calculate_ir_withholding(cls, monthly_taxable: float, constants: LegalYear,
                                 gastos: float = 0.0, cargas: int = 0,
                                 catastrophic: bool = False) -> float:
        """Retención mensual del IR por el método de proyección anual.

        Proyecta el ingreso gravable anual (sueldo mensual x 12), descuenta el
        aporte personal al IESS, aplica la tabla del IR y resta la rebaja por
        gastos personales; el impuesto anual resultante se divide en 12 meses.
        Los décimos y los fondos de reserva son exentos: no entran en la base.
        """
        annual_taxable = monthly_taxable * 12
        annual_iess = annual_taxable * constants.iess_employee
        base_imponible = annual_taxable - annual_iess
        annual_tax = cls.calculate_ir_tax(base_imponible, constants)
        rebate = cls.calculate_personal_expenses_rebate(gastos, cargas, constants, catastrophic)
        annual_tax = max(0.0, annual_tax - rebate)
        return annual_tax / 12

    # --- Cálculo mensual completo ----------------------------------------

    @classmethod
    def process_monthly_payroll(
        cls,
        employee: Employee,
        events: List[PayrollEvent],
        current_date: Optional[datetime] = None,
        period: Optional[str] = None,
    ) -> Dict:
        # Evita un default mutable/evaluado una sola vez: resolver "now" en cada llamada.
        if current_date is None:
            current_date = datetime.now()

        # Resolver el año (y por tanto las constantes legales) desde el período
        # YYYY-MM si viene; si no, desde la fecha de referencia.
        year = int(period[:4]) if period else current_date.year
        constants = legal_constants.for_year(year)

        taxable_earnings = employee.salary
        deductions_total = 0.0
        valor_hora = _value_per_hour(employee.salary)

        earnings_breakdown = {"base_salary": employee.salary}
        deductions_breakdown = {}

        for event in events:
            if event.type in _FLAT_EARNING_TYPES:
                # Ingreso gravable a monto fijo.
                taxable_earnings += event.amount
                earnings_breakdown[event.type.value] = event.amount
            elif event.type == EventType.HORAS_SUPLEMENTARIAS:
                # amount = nº de horas; el monto se calcula con recargo del 50%.
                pago = event.amount * valor_hora * SUPPLEMENTARY_SURCHARGE
                taxable_earnings += pago
                earnings_breakdown[event.type.value] = pago
            elif event.type == EventType.HORAS_EXTRAORDINARIAS:
                pago = event.amount * valor_hora * EXTRAORDINARY_SURCHARGE
                taxable_earnings += pago
                earnings_breakdown[event.type.value] = pago
            elif event.type == EventType.MULTA:
                # Tope legal: la multa no puede exceder el 10% de la remuneración.
                monto = min(event.amount, MULTA_CAP_RATE * employee.salary)
                deductions_total += monto
                deductions_breakdown[event.type.value] = monto
            elif event.type == EventType.FALTA:
                # amount = nº de horas no trabajadas; se descuenta el valor hora.
                monto = event.amount * valor_hora
                deductions_total += monto
                deductions_breakdown[event.type.value] = monto
            elif event.type in _FLAT_DEDUCTION_TYPES:
                deductions_total += event.amount
                # El descuento genérico usa su descripción; los demás, su etiqueta.
                label = event.description if event.type == EventType.DEDUCTION else event.type.value
                deductions_breakdown[label] = event.amount

        # IESS
        iess_employee = cls.calculate_iess_employee(taxable_earnings, constants)
        iess_employer = cls.calculate_iess_employer(taxable_earnings, constants)
        deductions_breakdown["IESS Personal (9.45%)"] = iess_employee

        # Impuesto a la Renta (retención mensual)
        income_tax = cls.calculate_ir_withholding(
            taxable_earnings, constants,
            gastos=employee.projected_personal_expenses,
            cargas=employee.family_burdens,
            catastrophic=employee.catastrophic_illness_burden,
        )
        if income_tax > 0:
            deductions_breakdown["Impuesto a la Renta"] = income_tax

        # Provisiones
        thirteenth = cls.calculate_thirteenth(taxable_earnings)

        region = employee.region_override or Region.SIERRA  # fallback por defecto
        fourteenth = cls.calculate_fourteenth(constants)

        # Normaliza tz-awareness: Firestore devuelve datetimes tz-aware mientras
        # un "now" naive puede pasarse. Quitar tzinfo de ambos antes de restar.
        ref_date = current_date.replace(tzinfo=None) if current_date.tzinfo else current_date
        start_date = employee.start_date.replace(tzinfo=None) if employee.start_date.tzinfo else employee.start_date
        years_of_service = (ref_date - start_date).days / 365.25
        reserve_funds = cls.calculate_reserve_funds(taxable_earnings, years_of_service, constants)

        vacations = cls.calculate_vacations(taxable_earnings)

        net_salary = taxable_earnings - iess_employee - income_tax - deductions_total

        # Mensualización de décimos: si NO se acumula, el 1/12 se paga cada mes
        # y se suma al líquido (los décimos siguen siendo exentos de IR).
        if not employee.accumulate_13th:
            net_salary += thirteenth
            earnings_breakdown["Décimo Tercero (mensualizado)"] = thirteenth
        if not employee.accumulate_14th:
            net_salary += fourteenth
            earnings_breakdown["Décimo Cuarto (mensualizado)"] = fourteenth

        return {
            "employee_id": employee.id,
            "taxable_earnings": taxable_earnings,
            "iess_employee": iess_employee,
            "iess_employer": iess_employer,
            "income_tax": income_tax,
            "thirteenth_salary": thirteenth,
            "fourteenth_salary": fourteenth,
            "fourteenth_payout_month": cls.fourteenth_payout_month(region),
            "reserve_funds": reserve_funds,
            "vacation_provision": vacations,
            "earnings_breakdown": earnings_breakdown,
            "deductions_breakdown": deductions_breakdown,
            "net_salary": net_salary,
        }

    # --- Liquidación de haberes (finiquito) ------------------------------

    @classmethod
    def calculate_settlement(
        cls,
        employee: Employee,
        termination_date: datetime,
        cause: SettlementCause,
        remuneration: Optional[float] = None,
        pending_vacation_days: float = 0.0,
        pending_reserve_funds: float = 0.0,
        unpaid_amounts: float = 0.0,
    ) -> Dict:
        """Calcula la liquidación de haberes al terminar la relación laboral.

        Componentes: décimos proporcionales, vacaciones proporcionales (Art. 78),
        fondos de reserva pendientes y, según la causa, la indemnización por
        despido (Art. 188) y/o la bonificación por desahucio (Art. 185). El total
        no descuenta aportes: es valor a recibir.

        `remuneration` es la base de cálculo (sueldo + beneficios permanentes);
        si no se pasa, se usa `employee.salary`. El décimo cuarto siempre usa el SBU.
        """
        term = _as_date(termination_date)
        hire = _as_date(employee.start_date)
        # "Remuneración" = sueldo + beneficios permanentes. El modelo solo guarda
        # `salary`; se permite sobrescribir con la remuneración real.
        remuneration = remuneration if remuneration is not None else employee.salary
        constants = legal_constants.for_year(term.year)
        region = employee.region_override or Region.SIERRA

        # Tiempo de servicio en años de CALENDARIO (no días/365.25) para evitar
        # error de redondeo en los límites de año.
        full_years = term.year - hire.year - (
            1 if (term.month, term.day) < (hire.month, hire.day) else 0
        )
        full_years = max(0, full_years)
        exact_years = (term.month, term.day) == (hire.month, hire.day)
        # Art. 188: la fracción de año se considera año completo.
        years_with_fraction = full_years if exact_years else full_years + 1
        years_float = max(0.0, (term - hire).days / 365.25)

        # Décimos proporcionales (un año completo = 1 remuneración / 1 SBU).
        days_13 = min(360, _prorated_days(_thirteenth_cycle_start(term), hire, term))
        thirteenth = remuneration * days_13 / 360
        days_14 = min(360, _prorated_days(_fourteenth_cycle_start(term, region), hire, term))
        fourteenth = constants.sbu * days_14 / 360

        # Vacaciones no gozadas (Art. 71): la veinticuatroava parte de lo percibido
        # en el año (equivale a remuneración/30 por día x 15 días/año), proporcional
        # al tiempo trabajado; más días no gozados de años anteriores. Por defecto
        # `remuneration`=sueldo, pero Art. 71 incluye horas extras y retribución
        # accesoria normal (excluye 13º/14º) si se pasa la remuneración ampliada.
        days_since_anniv = (term - _last_anniversary(hire, term)).days
        prop_vacation_days = 15.0 * (days_since_anniv / 365)
        total_vacation_days = prop_vacation_days + pending_vacation_days
        vacation = (remuneration / 30) * total_vacation_days

        # Indemnización / bonificación según la causa de salida.
        indemnizacion = 0.0
        desahucio_bonus = 0.0
        if cause == SettlementCause.DESPIDO_INTEMPESTIVO:
            # Art. 188: hasta 3 años → 3 meses; luego 1 mes por año (años con
            # fracción), máx 25 meses. ADEMÁS, bonificación del 25% (Art. 185).
            months = 3 if years_with_fraction <= 3 else min(years_with_fraction, 25)
            indemnizacion = remuneration * months
            desahucio_bonus = 0.25 * remuneration * full_years
        elif cause == SettlementCause.DESAHUCIO_TRABAJADOR:
            # Art. 185: 25% de la remuneración SOLO por años COMPLETOS (las
            # fracciones de año no cuentan para este rubro).
            desahucio_bonus = 0.25 * remuneration * full_years
        # RENUNCIA (Art. 180): solo proporcionales, sin indemnización.

        total = (
            thirteenth + fourteenth + vacation + pending_reserve_funds
            + indemnizacion + desahucio_bonus + unpaid_amounts
        )

        return {
            "employee_id": employee.id,
            "termination_date": term.isoformat(),
            "cause": cause.value,
            "years_of_service": round(years_float, 2),
            "full_years": full_years,
            "years_with_fraction": years_with_fraction,
            "thirteenth_proportional": thirteenth,
            "fourteenth_proportional": fourteenth,
            "vacation_pending_days": round(total_vacation_days, 2),
            "vacation_pending": vacation,
            "reserve_funds_pending": pending_reserve_funds,
            "severance_indemnity": indemnizacion,
            "desahucio_bonus": desahucio_bonus,
            "unpaid_amounts": unpaid_amounts,
            "total": total,
        }
