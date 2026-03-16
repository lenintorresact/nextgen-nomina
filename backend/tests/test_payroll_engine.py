import pytest
from datetime import datetime
from app.models.schemas import Employee, ContractType, Region, PayrollEvent, EventType
from app.services.payroll_engine import PayrollEngine

def test_basic_payroll_calculation():
    employee = Employee(
        id="emp123",
        company_id="comp1",
        cedula="1712345678",
        first_name="Juan",
        last_name="Perez",
        email="juan@example.com",
        salary=1000.0,
        start_date=datetime(2020, 1, 1),
        contract_type=ContractType.INDEFINITE,
        region_override=Region.SIERRA
    )

    events = []

    result = PayrollEngine.process_monthly_payroll(employee, events)

    assert result["taxable_earnings"] == 1000.0
    assert result["iess_employee"] == 94.5
    assert result["iess_employer"] == 121.5
    assert pytest.approx(result["thirteenth_salary"]) == 1000.0 / 12
    assert result["fourteenth_salary"] == 460.0 / 12
    assert result["reserve_funds"] == 83.3
    assert pytest.approx(result["vacation_provision"]) == 1000.0 / 24
    assert result["net_salary"] == 1000.0 - 94.5

def test_payroll_with_overtime():
    employee = Employee(
        id="emp123",
        company_id="comp1",
        cedula="1712345678",
        first_name="Juan",
        last_name="Perez",
        email="juan@example.com",
        salary=1000.0,
        start_date=datetime(2020, 1, 1),
        contract_type=ContractType.INDEFINITE
    )

    events = [
        PayrollEvent(
            employee_id="emp123",
            company_id="comp1",
            type=EventType.OVERTIME_50,
            amount=100.0,
            description="Extra hours",
            date=datetime.now()
        )
    ]

    result = PayrollEngine.process_monthly_payroll(employee, events)

    assert result["taxable_earnings"] == 1100.0
    assert result["iess_employee"] == 1100.0 * 0.0945
    assert result["net_salary"] == 1100.0 - (1100.0 * 0.0945)

def test_no_reserve_funds_for_new_employees():
    employee = Employee(
        id="emp123",
        company_id="comp1",
        cedula="1712345678",
        first_name="Juan",
        last_name="Perez",
        email="juan@example.com",
        salary=1000.0,
        start_date=datetime.now(), # Just started
        contract_type=ContractType.INDEFINITE
    )

    result = PayrollEngine.process_monthly_payroll(employee, [])
    assert result["reserve_funds"] == 0.0
