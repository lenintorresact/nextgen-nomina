from datetime import datetime
from typing import List, Dict, Optional
from ..models.schemas import Employee, PayrollEvent, EventType, Region

# 2024 Constants for Ecuador
SBU = 460.0  # Salario Básico Unificado 2024
IESS_EMPLOYEE_RATE = 0.0945
IESS_EMPLOYER_RATE = 0.1215
RESERVE_FUNDS_RATE = 0.0833

class PayrollEngine:
    @staticmethod
    def calculate_thirteenth(monthly_earnings: float) -> float:
        return monthly_earnings / 12

    @staticmethod
    def calculate_fourteenth(region: Region) -> float:
        # Simplified: SBU / 12.
        # In reality, it depends on the calculation period (Sierra vs Costa)
        # but for monthly provision, it is SBU / 12
        return SBU / 12

    @staticmethod
    def calculate_iess_employee(taxable_earnings: float) -> float:
        return taxable_earnings * IESS_EMPLOYEE_RATE

    @staticmethod
    def calculate_iess_employer(taxable_earnings: float) -> float:
        return taxable_earnings * IESS_EMPLOYER_RATE

    @staticmethod
    def calculate_reserve_funds(taxable_earnings: float, years_of_service: float) -> float:
        if years_of_service >= 1.0:
            return taxable_earnings * RESERVE_FUNDS_RATE
        return 0.0

    @staticmethod
    def calculate_vacations(taxable_earnings: float) -> float:
        return taxable_earnings / 24

    @classmethod
    def process_monthly_payroll(
        cls,
        employee: Employee,
        events: List[PayrollEvent],
        current_date: Optional[datetime] = None
    ) -> Dict:
        # Avoid a mutable/once-evaluated default: resolve "now" on every call.
        if current_date is None:
            current_date = datetime.now()

        taxable_earnings = employee.salary
        other_earnings = 0.0
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
        iess_employee = cls.calculate_iess_employee(taxable_earnings)
        iess_employer = cls.calculate_iess_employer(taxable_earnings)
        deductions_breakdown["IESS Personal (9.45%)"] = iess_employee

        # Provisions
        thirteenth = cls.calculate_thirteenth(taxable_earnings)

        region = employee.region_override or Region.SIERRA # Default fallback
        fourteenth = cls.calculate_fourteenth(region)

        # Normalize tz-awareness: Firestore returns tz-aware datetimes while a
        # naive "now" may be passed in. Strip tzinfo from both before subtracting.
        ref_date = current_date.replace(tzinfo=None) if current_date.tzinfo else current_date
        start_date = employee.start_date.replace(tzinfo=None) if employee.start_date.tzinfo else employee.start_date
        years_of_service = (ref_date - start_date).days / 365.25
        reserve_funds = cls.calculate_reserve_funds(taxable_earnings, years_of_service)

        vacations = cls.calculate_vacations(taxable_earnings)

        net_salary = taxable_earnings - iess_employee - deductions_total

        return {
            "employee_id": employee.id,
            "taxable_earnings": taxable_earnings,
            "iess_employee": iess_employee,
            "iess_employer": iess_employer,
            "thirteenth_salary": thirteenth,
            "fourteenth_salary": fourteenth,
            "reserve_funds": reserve_funds,
            "vacation_provision": vacations,
            "earnings_breakdown": earnings_breakdown,
            "deductions_breakdown": deductions_breakdown,
            "net_salary": net_salary
        }
