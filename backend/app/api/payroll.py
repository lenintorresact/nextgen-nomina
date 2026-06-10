from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models.schemas import PayrollEvent, PayrollSlip, Employee
from ..core.config import db, get_current_user
from ..services.payroll_engine import PayrollEngine
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/payroll", tags=["payroll"])

# Ecuador's civil timezone. Used to derive the "current month" so a payroll
# period does not flip a day early when the server clock (UTC) crosses midnight.
EC_TZ = ZoneInfo("America/Guayaquil")


def _verify_company_ownership(company_id: str, user) -> dict:
    """Return the company doc dict if the caller owns it, else raise 403/404."""
    company_doc = db.collection("companies").document(company_id).get()
    if not company_doc.exists or company_doc.to_dict().get("owner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return company_doc.to_dict()


def _employee_events_for_period(employee_id: str, period: str) -> List[PayrollEvent]:
    """Events belonging to an employee that fall within a YYYY-MM period.

    Kept as a single-field query (by employee_id) plus an in-memory month
    filter on purpose: this avoids requiring a Firestore composite index.
    """
    events_docs = db.collection("events").where("employee_id", "==", employee_id).stream()
    events = [PayrollEvent(**{**ev.to_dict(), "id": ev.id}) for ev in events_docs]
    return [e for e in events if e.date.strftime("%Y-%m") == period]

@router.post("/events", response_model=PayrollEvent)
async def log_event(event: PayrollEvent, user=Depends(get_current_user)):
    # Verify ownership via company
    _verify_company_ownership(event.company_id, user)

    event_data = event.dict(exclude={"id"})
    doc_ref = db.collection("events").document()
    doc_ref.set(event_data)

    event.id = doc_ref.id
    return event


@router.get("/preview/{company_id}")
async def preview_payroll(company_id: str, period: str = None, user=Depends(get_current_user)):
    """Live, non-persisting payroll calculation for a company.

    This powers the core demo concept: as soon as an event is logged, the
    running monthly totals recalculate — no need to "close" the period.
    Defaults to the current month in Ecuador's timezone.
    """
    _verify_company_ownership(company_id, user)

    now_ec = datetime.now(EC_TZ)
    if not period:
        period = now_ec.strftime("%Y-%m")

    employees_docs = db.collection("employees").where("company_id", "==", company_id).stream()

    employees_preview = []
    company_totals = {
        "net_salary": 0.0,
        "iess_employee": 0.0,
        "iess_employer": 0.0,
        "thirteenth_salary": 0.0,
        "fourteenth_salary": 0.0,
        "reserve_funds": 0.0,
        "vacation_provision": 0.0,
    }

    for emp_doc in employees_docs:
        emp_data = emp_doc.to_dict()
        emp_data["id"] = emp_doc.id
        employee = Employee(**emp_data)

        period_events = _employee_events_for_period(employee.id, period)
        calc = PayrollEngine.process_monthly_payroll(employee, period_events, current_date=now_ec)

        employees_preview.append({
            "employee_id": employee.id,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "base_salary": employee.salary,
            **calc,
        })

        for key in company_totals:
            company_totals[key] += calc.get(key, 0.0)

    return {
        "company_id": company_id,
        "period": period,
        "employee_count": len(employees_preview),
        "employees": employees_preview,
        "totals": company_totals,
    }

@router.post("/close-period/{company_id}/{period}", response_model=List[PayrollSlip])
async def close_period(company_id: str, period: str, user=Depends(get_current_user)):
    # Verify ownership
    _verify_company_ownership(company_id, user)

    # Get all employees for company
    employees_docs = db.collection("employees").where("company_id", "==", company_id).stream()

    slips = []
    for emp_doc in employees_docs:
        emp_data = emp_doc.to_dict()
        emp_data["id"] = emp_doc.id
        employee = Employee(**emp_data)

        period_events = _employee_events_for_period(employee.id, period)

        calculation = PayrollEngine.process_monthly_payroll(
            employee, period_events, current_date=datetime.now(EC_TZ)
        )

        slip_data = {
            "employee_id": employee.id,
            "company_id": company_id,
            "period": period,
            "base_salary": employee.salary,
            "earnings": calculation["earnings_breakdown"],
            "deductions": calculation["deductions_breakdown"],
            "net_salary": calculation["net_salary"],
            "iess_employee": calculation["iess_employee"],
            "iess_employer": calculation["iess_employer"],
            "thirteenth_salary": calculation["thirteenth_salary"],
            "fourteenth_salary": calculation["fourteenth_salary"],
            "reserve_funds": calculation["reserve_funds"],
            "vacation_provision": calculation["vacation_provision"],
            "status": "closed"
        }

        doc_ref = db.collection("slips").document()
        doc_ref.set(slip_data)
        slip_data["id"] = doc_ref.id
        slips.append(PayrollSlip(**slip_data))

    return slips
