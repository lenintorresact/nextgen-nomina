from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from ..models.schemas import PayrollEvent, PayrollSlip, Employee, SettlementCause
from ..core.config import db, get_current_user
from ..services.payroll_engine import PayrollEngine
from ..services import pdf_reports, legal_constants
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


def _current_period(company: dict) -> str:
    """Período abierto actual de la empresa; por defecto el mes calendario (EC)."""
    return company.get("current_period") or datetime.now(EC_TZ).strftime("%Y-%m")


def _next_period(period: str) -> str:
    """Siguiente período YYYY-MM."""
    year, month = int(period[:4]), int(period[5:7])
    return f"{year + 1}-01" if month == 12 else f"{year}-{month + 1:02d}"


def _delete_company_slips_for_period(company_id: str, period: str) -> None:
    """Borra los roles persistidos de una empresa en un período (cierre idempotente)."""
    docs = db.collection("slips").where("company_id", "==", company_id).stream()
    for d in docs:
        if d.to_dict().get("period") == period:
            d.reference.delete()


def _employee_events_for_period(employee_id: str, period: str) -> List[PayrollEvent]:
    """Events belonging to an employee that fall within a YYYY-MM period.

    Kept as a single-field query (by employee_id) plus an in-memory month
    filter on purpose: this avoids requiring a Firestore composite index.
    El período de una novedad es su campo `period` si existe; si no (eventos
    antiguos), se deriva de la fecha.
    """
    events_docs = db.collection("events").where("employee_id", "==", employee_id).stream()
    events = [PayrollEvent(**{**ev.to_dict(), "id": ev.id}) for ev in events_docs]
    return [e for e in events if (e.period or e.date.strftime("%Y-%m")) == period]

@router.post("/events", response_model=PayrollEvent)
async def log_event(event: PayrollEvent, user=Depends(get_current_user)):
    # Verify ownership via company
    company = _verify_company_ownership(event.company_id, user)

    # Sella la novedad con el período abierto actual: tras un cierre, las nuevas
    # novedades caen en el siguiente período aunque su fecha sea del mes cerrado.
    if not event.period:
        event.period = _current_period(company)

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
    company = _verify_company_ownership(company_id, user)

    now_ec = datetime.now(EC_TZ)
    if not period:
        period = _current_period(company)

    employees_docs = db.collection("employees").where("company_id", "==", company_id).stream()

    employees_preview = []
    company_totals = {
        "net_salary": 0.0,
        "iess_employee": 0.0,
        "iess_employer": 0.0,
        "income_tax": 0.0,
        "thirteenth_salary": 0.0,
        "fourteenth_salary": 0.0,
        "reserve_funds": 0.0,
        "vacation_provision": 0.0,
    }

    for emp_doc in employees_docs:
        emp_data = emp_doc.to_dict()
        emp_data["id"] = emp_doc.id
        employee = Employee(**emp_data)

        if not employee.active:
            # Dado de baja en el período abierto: se muestra deshabilitado, sin
            # entrar en los totales. Si la baja es de un período ya cerrado, se omite.
            if employee.termination_period == period:
                employees_preview.append({
                    "employee_id": employee.id,
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "base_salary": employee.salary,
                    "net_salary": 0.0,
                    "terminated": True,
                })
            continue

        period_events = _employee_events_for_period(employee.id, period)
        calc = PayrollEngine.process_monthly_payroll(
            employee, period_events, current_date=now_ec, period=period
        )

        employees_preview.append({
            "employee_id": employee.id,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "base_salary": employee.salary,
            "terminated": False,
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
    company = _verify_company_ownership(company_id, user)

    # Progresión lineal: solo se puede cerrar el período abierto actual.
    open_period = _current_period(company)
    if period != open_period:
        raise HTTPException(
            status_code=400,
            detail=f"Solo puedes cerrar el período abierto ({open_period}).",
        )

    # Cierre idempotente: si ya había roles de este período (re-cierre), se borran
    # antes de regenerarlos para no duplicar.
    _delete_company_slips_for_period(company_id, period)

    # Get all employees for company
    employees_docs = db.collection("employees").where("company_id", "==", company_id).stream()

    slips = []
    for emp_doc in employees_docs:
        emp_data = emp_doc.to_dict()
        emp_data["id"] = emp_doc.id
        employee = Employee(**emp_data)

        # Los empleados dados de baja no generan rol mensual (su finiquito es aparte).
        if not employee.active:
            continue

        period_events = _employee_events_for_period(employee.id, period)

        calculation = PayrollEngine.process_monthly_payroll(
            employee, period_events, current_date=datetime.now(EC_TZ), period=period
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
            "income_tax": calculation["income_tax"],
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

    # Marca el período como cerrado y avanza el período abierto al siguiente mes.
    closed = company.get("closed_periods") or []
    if period not in closed:
        closed.append(period)
    db.collection("companies").document(company_id).update({
        "closed_periods": closed,
        "current_period": _next_period(period),
    })

    return slips


@router.post("/reopen-period/{company_id}/{period}")
async def reopen_period(company_id: str, period: str, user=Depends(get_current_user)):
    """Reabre el período cerrado más reciente (rollback lineal).

    Borra los roles persistidos de ese período y vuelve a ponerlo como período
    abierto, de modo que se puedan registrar/corregir novedades nuevamente.
    """
    company = _verify_company_ownership(company_id, user)
    closed = company.get("closed_periods") or []

    # Solo se reabre el período inmediatamente anterior al abierto (lineal).
    if period not in closed or _next_period(period) != _current_period(company):
        raise HTTPException(
            status_code=400,
            detail="Solo puedes reabrir el último período cerrado.",
        )

    _delete_company_slips_for_period(company_id, period)
    closed = [p for p in closed if p != period]
    db.collection("companies").document(company_id).update({
        "closed_periods": closed,
        "current_period": period,
    })

    return {"company_id": company_id, "current_period": period, "closed_periods": closed}


@router.get("/settlement/{employee_id}")
async def settlement(
    employee_id: str,
    termination_date: str,
    cause: SettlementCause,
    remuneration: float | None = None,
    pending_vacation_days: float = 0.0,
    pending_reserve_funds: float = 0.0,
    unpaid_amounts: float = 0.0,
    user=Depends(get_current_user),
):
    """Liquidación de haberes (finiquito) para un empleado.

    `termination_date` en formato YYYY-MM-DD. No persiste: es un cálculo en vivo
    como el preview mensual.
    """
    emp_doc = db.collection("employees").document(employee_id).get()
    if not emp_doc.exists:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp_data = emp_doc.to_dict()
    emp_data["id"] = emp_doc.id
    # Verifica que el usuario sea dueño de la empresa del empleado.
    _verify_company_ownership(emp_data["company_id"], user)
    employee = Employee(**emp_data)

    try:
        term = datetime.strptime(termination_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="termination_date must be YYYY-MM-DD")

    return PayrollEngine.calculate_settlement(
        employee,
        term,
        cause,
        remuneration=remuneration,
        pending_vacation_days=pending_vacation_days,
        pending_reserve_funds=pending_reserve_funds,
        unpaid_amounts=unpaid_amounts,
    )


def _load_owned_employee(employee_id: str, user) -> tuple:
    """Devuelve (employee, company_dict) verificando propiedad, o lanza 404/403."""
    emp_doc = db.collection("employees").document(employee_id).get()
    if not emp_doc.exists:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp_data = emp_doc.to_dict()
    emp_data["id"] = emp_doc.id
    company = _verify_company_ownership(emp_data["company_id"], user)
    return Employee(**emp_data), company


@router.post("/terminate/{employee_id}")
async def terminate_employee(
    employee_id: str,
    termination_date: str,
    cause: SettlementCause,
    remuneration: float | None = None,
    pending_vacation_days: float = 0.0,
    pending_reserve_funds: float = 0.0,
    unpaid_amounts: float = 0.0,
    user=Depends(get_current_user),
):
    """Registra el finiquito y da de baja al empleado en el período abierto.

    Persiste la liquidación (colección `settlements`, un doc por empleado) y marca
    el empleado como inactivo. Mientras no se cierre el período, la baja es
    reversible vía /reactivate.
    """
    employee, company = _load_owned_employee(employee_id, user)
    try:
        term = datetime.strptime(termination_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="termination_date must be YYYY-MM-DD")

    settlement = PayrollEngine.calculate_settlement(
        employee, term, cause,
        remuneration=remuneration,
        pending_vacation_days=pending_vacation_days,
        pending_reserve_funds=pending_reserve_funds,
        unpaid_amounts=unpaid_amounts,
    )

    period = _current_period(company)
    db.collection("settlements").document(employee_id).set({
        "employee_id": employee_id,
        "company_id": employee.company_id,
        "period": period,
        "termination_date": termination_date,
        "cause": cause.value,
        **settlement,
    })
    db.collection("employees").document(employee_id).update({
        "active": False,
        "termination_date": term,
        "termination_cause": cause.value,
        "termination_period": period,
    })

    return settlement


@router.post("/reactivate/{employee_id}")
async def reactivate_employee(employee_id: str, user=Depends(get_current_user)):
    """Revierte una baja, solo si ocurrió en el período abierto actual."""
    employee, company = _load_owned_employee(employee_id, user)
    if employee.active:
        raise HTTPException(status_code=400, detail="El empleado no está dado de baja.")
    if employee.termination_period != _current_period(company):
        raise HTTPException(
            status_code=400,
            detail="Solo puedes reactivar una baja del período abierto actual.",
        )

    db.collection("employees").document(employee_id).update({
        "active": True,
        "termination_date": None,
        "termination_cause": None,
        "termination_period": None,
    })
    db.collection("settlements").document(employee_id).delete()
    return {"employee_id": employee_id, "active": True}


@router.get("/settlement-record/{employee_id}")
async def settlement_record(employee_id: str, user=Depends(get_current_user)):
    """Recupera el finiquito guardado de un empleado dado de baja (para revisión)."""
    _load_owned_employee(employee_id, user)
    rec = db.collection("settlements").document(employee_id).get()
    if not rec.exists:
        raise HTTPException(status_code=404, detail="No hay finiquito registrado.")
    return rec.to_dict()


@router.get("/settlement-comparison/{employee_id}")
async def settlement_comparison(
    employee_id: str,
    termination_date: str,
    remuneration: float | None = None,
    pending_vacation_days: float = 0.0,
    pending_reserve_funds: float = 0.0,
    unpaid_amounts: float = 0.0,
    user=Depends(get_current_user),
):
    """Liquidación calculada para CADA causa de salida, para comparar opciones.

    Mismos parámetros que /settlement pero sin `cause`: devuelve un resultado por
    cada causa válida, de modo que el usuario elija con el costo a la vista.
    """
    employee, _ = _load_owned_employee(employee_id, user)
    try:
        term = datetime.strptime(termination_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="termination_date must be YYYY-MM-DD")

    return [
        PayrollEngine.calculate_settlement(
            employee, term, cause,
            remuneration=remuneration,
            pending_vacation_days=pending_vacation_days,
            pending_reserve_funds=pending_reserve_funds,
            unpaid_amounts=unpaid_amounts,
        )
        for cause in SettlementCause
    ]


@router.get("/payslip/{company_id}/{employee_id}/pdf")
async def payslip_pdf(company_id: str, employee_id: str, period: str = None,
                      user=Depends(get_current_user)):
    """Rol de pagos individual (PDF) de un empleado. Se recalcula en vivo."""
    company = _verify_company_ownership(company_id, user)
    company["id"] = company_id
    now_ec = datetime.now(EC_TZ)
    if not period:
        period = now_ec.strftime("%Y-%m")

    emp_doc = db.collection("employees").document(employee_id).get()
    if not emp_doc.exists or emp_doc.to_dict().get("company_id") != company_id:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp_data = emp_doc.to_dict()
    emp_data["id"] = emp_doc.id
    employee = Employee(**emp_data)

    period_events = _employee_events_for_period(employee.id, period)
    calc = PayrollEngine.process_monthly_payroll(
        employee, period_events, current_date=now_ec, period=period)

    pdf = pdf_reports.build_payslip_pdf(company, employee, calc, period)
    filename = f"rol_{employee.cedula}_{period}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"inline; filename={filename}"})


@router.get("/payroll-report/{company_id}/pdf")
async def payroll_report_pdf(company_id: str, period: str = None,
                             user=Depends(get_current_user)):
    """Rol de pagos consolidado (PDF) de toda la empresa para un período."""
    company = _verify_company_ownership(company_id, user)
    company["id"] = company_id
    now_ec = datetime.now(EC_TZ)
    if not period:
        period = now_ec.strftime("%Y-%m")

    employees_docs = db.collection("employees").where("company_id", "==", company_id).stream()

    rows = []
    totals = {"net_salary": 0.0, "iess_employee": 0.0, "income_tax": 0.0}
    for emp_doc in employees_docs:
        emp_data = emp_doc.to_dict()
        emp_data["id"] = emp_doc.id
        employee = Employee(**emp_data)

        period_events = _employee_events_for_period(employee.id, period)
        calc = PayrollEngine.process_monthly_payroll(
            employee, period_events, current_date=now_ec, period=period)

        rows.append({
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "base_salary": employee.salary,
            **calc,
        })
        for key in totals:
            totals[key] += calc.get(key, 0.0)

    pdf = pdf_reports.build_consolidated_pdf(company, rows, period, totals)
    filename = f"rol_consolidado_{period}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"inline; filename={filename}"})


@router.get("/planilla-iess/{company_id}/pdf")
async def planilla_iess_pdf(company_id: str, period: str = None,
                            user=Depends(get_current_user)):
    """Planilla de aportes IESS (PDF) de la empresa para un período."""
    company = _verify_company_ownership(company_id, user)
    company["id"] = company_id
    now_ec = datetime.now(EC_TZ)
    if not period:
        period = now_ec.strftime("%Y-%m")
    constants = legal_constants.for_year(int(period[:4]))

    employees_docs = db.collection("employees").where("company_id", "==", company_id).stream()

    rows = []
    for emp_doc in employees_docs:
        emp_data = emp_doc.to_dict()
        emp_data["id"] = emp_doc.id
        employee = Employee(**emp_data)

        period_events = _employee_events_for_period(employee.id, period)
        calc = PayrollEngine.process_monthly_payroll(
            employee, period_events, current_date=now_ec, period=period)

        rows.append({
            "cedula": employee.cedula,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "days": 30,  # el run mensual no registra días trabajados; se asume mes completo
            "taxable": calc["taxable_earnings"],
            "reserve_funds": calc["reserve_funds"],
        })

    pdf = pdf_reports.build_planilla_iess_pdf(company, rows, period, constants)
    filename = f"planilla_iess_{period}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"inline; filename={filename}"})


def _annual_form107_data(employee: Employee, year: int, constants) -> tuple:
    """Agrega los valores anuales del Formulario 107 para un empleado.

    Suma los roles cerrados del ejercicio; si no hay ninguno, proyecta el mes
    actual × 12 (devuelve projected=True). Reconstruye los ingresos gravables a
    partir del aporte personal IESS (que se cobra exactamente sobre la base).
    """
    slips = db.collection("slips").where("employee_id", "==", employee.id).stream()
    year_slips = [s.to_dict() for s in slips if str(s.to_dict().get("period", "")).startswith(str(year))]

    projected = False
    if year_slips:
        aporte_iess = sum(s.get("iess_employee", 0.0) for s in year_slips)
        ir_retenido = sum(s.get("income_tax", 0.0) for s in year_slips)
        ingresos_gravados = aporte_iess / constants.iess_employee if constants.iess_employee else 0.0
    else:
        # Proyección: mes representativo × 12.
        projected = True
        calc = PayrollEngine.process_monthly_payroll(employee, [], period=f"{year}-01")
        ingresos_gravados = calc["taxable_earnings"] * 12
        aporte_iess = calc["iess_employee"] * 12
        ir_retenido = calc["income_tax"] * 12

    base_imponible = max(0.0, ingresos_gravados - aporte_iess)
    impuesto_bruto = PayrollEngine.calculate_ir_tax(base_imponible, constants)
    rebaja = PayrollEngine.calculate_personal_expenses_rebate(
        employee.projected_personal_expenses, employee.family_burdens, constants,
        employee.catastrophic_illness_burden)
    impuesto_neto = max(0.0, impuesto_bruto - rebaja)

    data = {
        "ingresos_gravados": ingresos_gravados,
        "sobresueldos": 0.0,  # no se separa del total en este sistema
        "aporte_iess": aporte_iess,
        "base_imponible": base_imponible,
        "impuesto_causado_bruto": impuesto_bruto,
        "rebaja_gastos": rebaja,
        "impuesto_causado_neto": impuesto_neto,
        "impuesto_retenido": ir_retenido,
        "impuesto_asumido": 0.0,
    }
    return data, projected


@router.get("/form107/{company_id}/{employee_id}/pdf")
async def form107_pdf(company_id: str, employee_id: str, year: int = None,
                      user=Depends(get_current_user)):
    """Comprobante de retenciones (Formulario 107) anual de un empleado (PDF)."""
    company = _verify_company_ownership(company_id, user)
    company["id"] = company_id
    if not year:
        year = datetime.now(EC_TZ).year

    emp_doc = db.collection("employees").document(employee_id).get()
    if not emp_doc.exists or emp_doc.to_dict().get("company_id") != company_id:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp_data = emp_doc.to_dict()
    emp_data["id"] = emp_doc.id
    employee = Employee(**emp_data)

    constants = legal_constants.for_year(year)
    data, projected = _annual_form107_data(employee, year, constants)

    pdf = pdf_reports.build_form107_pdf(company, employee, data, year, projected=projected)
    filename = f"form107_{employee.cedula}_{year}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"inline; filename={filename}"})


@router.get("/decimos-report/{company_id}/pdf")
async def decimos_report_pdf(company_id: str, year: int = None,
                             user=Depends(get_current_user)):
    """Reporte de décimos (13º y 14º) de la empresa para un ejercicio (PDF)."""
    company = _verify_company_ownership(company_id, user)
    company["id"] = company_id
    if not year:
        year = datetime.now(EC_TZ).year
    constants = legal_constants.for_year(year)

    employees_docs = db.collection("employees").where("company_id", "==", company_id).stream()

    rows = []
    any_projected = False
    for emp_doc in employees_docs:
        emp_data = emp_doc.to_dict()
        emp_data["id"] = emp_doc.id
        employee = Employee(**emp_data)

        slips = db.collection("slips").where("employee_id", "==", employee.id).stream()
        year_slips = [s.to_dict() for s in slips
                      if str(s.to_dict().get("period", "")).startswith(str(year))]

        if year_slips:
            thirteenth = sum(s.get("thirteenth_salary", 0.0) for s in year_slips)
        else:
            # Proyección: provisión mensual del 13º × 12 ≈ una remuneración anual / 12.
            any_projected = True
            calc = PayrollEngine.process_monthly_payroll(employee, [], period=f"{year}-01")
            thirteenth = calc["thirteenth_salary"] * 12

        rows.append({
            "cedula": employee.cedula,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "thirteenth": thirteenth,
            "fourteenth": constants.sbu,  # 14º anual = 1 SBU (completo); prorratea si parcial
            "forma_13": "Acumulado" if employee.accumulate_13th else "Mensualizado",
            "forma_14": "Acumulado" if employee.accumulate_14th else "Mensualizado",
        })

    pdf = pdf_reports.build_decimos_pdf(company, rows, year, projected=any_projected)
    filename = f"decimos_{year}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"inline; filename={filename}"})
