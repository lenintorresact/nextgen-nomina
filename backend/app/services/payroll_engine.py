from datetime import datetime
from typing import List, Dict, Optional
from ..models.schemas import Employee, PayrollEvent, EventType, Region
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
                                           constants: LegalYear) -> float:
        """Rebaja por gastos personales: % sobre el menor entre los gastos
        declarados y el tope de N canastas básicas (según cargas familiares)."""
        if gastos <= 0:
            return 0.0
        tope = constants.canastas_for_cargas(cargas) * constants.canasta_basica
        return constants.gastos_rebate_rate * min(gastos, tope)

    @classmethod
    def calculate_ir_withholding(cls, monthly_taxable: float, constants: LegalYear,
                                 gastos: float = 0.0, cargas: int = 0) -> float:
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
        rebate = cls.calculate_personal_expenses_rebate(gastos, cargas, constants)
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

        earnings_breakdown = {"base_salary": employee.salary}
        deductions_breakdown = {}

        for event in events:
            if event.type in [EventType.OVERTIME_50, EventType.OVERTIME_100, EventType.COMMISSION, EventType.BONUS]:
                taxable_earnings += event.amount
                earnings_breakdown[event.type.value] = event.amount
            elif event.type == EventType.DEDUCTION:
                deductions_total += event.amount
                deductions_breakdown[event.description] = event.amount

        # IESS
        iess_employee = cls.calculate_iess_employee(taxable_earnings, constants)
        iess_employer = cls.calculate_iess_employer(taxable_earnings, constants)
        deductions_breakdown["IESS Personal (9.45%)"] = iess_employee

        # Impuesto a la Renta (retención mensual)
        income_tax = cls.calculate_ir_withholding(
            taxable_earnings, constants,
            gastos=employee.projected_personal_expenses,
            cargas=employee.family_burdens,
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
