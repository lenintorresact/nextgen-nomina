from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models.schemas import PayrollEvent, PayrollSlip, Employee
from ..core.config import db, get_current_user
from ..services.payroll_engine import PayrollEngine
from datetime import datetime

router = APIRouter(prefix="/payroll", tags=["payroll"])

@router.post("/events", response_model=PayrollEvent)
async def log_event(event: PayrollEvent, user=Depends(get_current_user)):
    # Verify ownership via company
    company_doc = db.collection("companies").document(event.company_id).get()
    if not company_doc.exists or company_doc.to_dict().get("owner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    event_data = event.dict(exclude={"id"})
    doc_ref = db.collection("events").document()
    doc_ref.set(event_data)

    event.id = doc_ref.id
    return event

@router.post("/close-period/{company_id}/{period}", response_model=List[PayrollSlip])
async def close_period(company_id: str, period: str, user=Depends(get_current_user)):
    # Verify ownership
    company_doc = db.collection("companies").document(company_id).get()
    if not company_doc.exists or company_doc.to_dict().get("owner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get all employees for company
    employees_docs = db.collection("employees").where("company_id", "==", company_id).stream()

    slips = []
    for emp_doc in employees_docs:
        emp_data = emp_doc.to_dict()
        emp_data["id"] = emp_doc.id
        employee = Employee(**emp_data)

        # Get events for this employee and period
        # Note: In a real scenario, we'd filter by date range for the period
        events_docs = db.collection("events").where("employee_id", "==", employee.id).stream()
        events = [PayrollEvent(**{**ev.to_dict(), "id": ev.id}) for ev in events_docs]

        # Filter events by period (simplified logic here)
        period_events = [e for e in events if e.date.strftime("%Y-%m") == period]

        calculation = PayrollEngine.process_monthly_payroll(employee, period_events)

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
