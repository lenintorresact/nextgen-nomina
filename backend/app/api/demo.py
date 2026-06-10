from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from ..core.config import db, get_current_user

router = APIRouter(prefix="/demo", tags=["demo"])

EC_TZ = ZoneInfo("America/Guayaquil")

# Empresa y empleados de ejemplo para que cualquier visitante pruebe el concepto
# sin tener que registrar datos. Sueldos y fechas de ingreso variados para que
# el 13º, 14º y los fondos de reserva difieran entre empleados.
SAMPLE_COMPANY = {
    "ruc": "1790012345001",
    "name": "Comercial El Sol Cía. Ltda.",
    "region": "Sierra",
}

SAMPLE_EMPLOYEES = [
    {
        "cedula": "1712345678",
        "first_name": "María",
        "last_name": "Cevallos",
        "email": "maria.cevallos@demo.ec",
        "salary": 850.0,
        "years_ago_hired": 3,
        "contract_type": "Indefinido",
    },
    {
        "cedula": "0923456789",
        "first_name": "Jorge",
        "last_name": "Andrade",
        "email": "jorge.andrade@demo.ec",
        "salary": 600.0,
        "years_ago_hired": 1,
        "contract_type": "Indefinido",
    },
    {
        "cedula": "1804567890",
        "first_name": "Lucía",
        "last_name": "Paredes",
        "email": "lucia.paredes@demo.ec",
        "salary": 460.0,
        "years_ago_hired": 0,  # ingreso reciente: aún sin fondos de reserva
        "contract_type": "Plazo Fijo",
    },
]


@router.post("/seed")
async def seed_demo(user=Depends(get_current_user)):
    """Crea datos de ejemplo para el usuario actual (incluye usuarios anónimos).

    Es idempotente: si el usuario ya tiene una empresa, la devuelve sin crear
    duplicados. Así, refrescar la página no genera empresas repetidas.
    """
    uid = user["uid"]

    existing = list(db.collection("companies").where("owner_id", "==", uid).limit(1).stream())
    if existing:
        doc = existing[0]
        return {"company_id": doc.id, "created": False, **doc.to_dict()}

    now_ec = datetime.now(EC_TZ)

    company_data = {**SAMPLE_COMPANY, "owner_id": uid}
    company_ref = db.collection("companies").document()
    company_ref.set(company_data)
    company_id = company_ref.id

    for emp in SAMPLE_EMPLOYEES:
        start_date = now_ec.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=int(emp["years_ago_hired"] * 365.25)
        )
        emp_ref = db.collection("employees").document()
        emp_ref.set({
            "company_id": company_id,
            "cedula": emp["cedula"],
            "first_name": emp["first_name"],
            "last_name": emp["last_name"],
            "email": emp["email"],
            "salary": emp["salary"],
            "start_date": start_date,
            "contract_type": emp["contract_type"],
            "accumulate_13th": True,
            "accumulate_14th": True,
            "accumulate_reserve_funds": True,
        })

        # Un par de novedades del mes en curso para que el cálculo en vivo
        # tenga algo que mostrar de inmediato. Día 10 para evitar bordes de mes.
        event_date = now_ec.replace(day=10, hour=12, minute=0, second=0, microsecond=0)
        if emp["salary"] >= 600.0:
            db.collection("events").document().set({
                "employee_id": emp_ref.id,
                "company_id": company_id,
                "type": "Overtime 50%",
                "amount": 75.0,
                "description": "Horas extras (ejemplo)",
                "date": event_date,
            })

    return {"company_id": company_id, "created": True, **company_data}
