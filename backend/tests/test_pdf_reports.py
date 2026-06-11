from datetime import datetime

from app.models.schemas import Employee, ContractType, Region
from app.services.payroll_engine import PayrollEngine
from app.services import pdf_reports

_COMPANY = {"id": "comp1", "name": "Acme S.A.", "ruc": "1790012345001", "region": "Sierra"}


def _employee():
    return Employee(
        id="emp123", company_id="comp1", cedula="1712345678",
        first_name="Juan", last_name="Perez", email="juan@example.com",
        salary=1500.0, start_date=datetime(2020, 1, 1),
        contract_type=ContractType.INDEFINITE, region_override=Region.SIERRA,
    )


def test_build_payslip_pdf_returns_pdf_bytes():
    emp = _employee()
    calc = PayrollEngine.process_monthly_payroll(emp, [], period="2026-06")
    pdf = pdf_reports.build_payslip_pdf(_COMPANY, emp, calc, "2026-06")
    assert isinstance(pdf, bytes) and len(pdf) > 0
    assert pdf[:4] == b"%PDF"


def test_build_consolidated_pdf_returns_pdf_bytes():
    emp = _employee()
    calc = PayrollEngine.process_monthly_payroll(emp, [], period="2026-06")
    rows = [{"first_name": emp.first_name, "last_name": emp.last_name,
             "base_salary": emp.salary, **calc}]
    totals = {
        "net_salary": calc["net_salary"],
        "iess_employee": calc["iess_employee"],
        "income_tax": calc["income_tax"],
    }
    pdf = pdf_reports.build_consolidated_pdf(_COMPANY, rows, "2026-06", totals)
    assert isinstance(pdf, bytes) and len(pdf) > 0
    assert pdf[:4] == b"%PDF"
