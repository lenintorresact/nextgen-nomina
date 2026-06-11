from datetime import datetime

import pytest

from app.models.schemas import Employee, ContractType, Region
from app.services.payroll_engine import PayrollEngine
from app.services import pdf_reports, legal_constants

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


def test_build_planilla_iess_pdf_returns_pdf_bytes():
    emp = _employee()
    calc = PayrollEngine.process_monthly_payroll(emp, [], period="2026-06")
    rows = [{
        "cedula": emp.cedula, "first_name": emp.first_name, "last_name": emp.last_name,
        "days": 30, "taxable": calc["taxable_earnings"], "reserve_funds": calc["reserve_funds"],
    }]
    pdf = pdf_reports.build_planilla_iess_pdf(
        _COMPANY, rows, "2026-06", legal_constants.for_year(2026))
    assert isinstance(pdf, bytes) and len(pdf) > 0
    assert pdf[:4] == b"%PDF"


def test_planilla_employer_breakdown_sums_to_total_rate():
    # El desglose patronal (11.15 + 0.5 + 0.5) debe sumar el patronal total (12.15%).
    c = legal_constants.for_year(2026)
    assert c.iess_employer_iess + c.iece_rate + c.secap_rate == pytest.approx(c.iess_employer)
