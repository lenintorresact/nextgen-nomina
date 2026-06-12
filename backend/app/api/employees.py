from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models.schemas import Employee
from ..core.config import db, get_current_user

router = APIRouter(prefix="/employees", tags=["employees"])

@router.post("/", response_model=Employee)
async def create_employee(employee: Employee, user=Depends(get_current_user)):
    # Check if user owns the company
    company_doc = db.collection("companies").document(employee.company_id).get()
    if not company_doc.exists or company_doc.to_dict().get("owner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized to add employee to this company")

    employee_data = employee.dict(exclude={"id"})
    doc_ref = db.collection("employees").document()
    doc_ref.set(employee_data)

    employee.id = doc_ref.id
    return employee

@router.get("/company/{company_id}", response_model=List[Employee])
async def get_company_employees(company_id: str, user=Depends(get_current_user)):
    # Check ownership
    company_doc = db.collection("companies").document(company_id).get()
    if not company_doc.exists or company_doc.to_dict().get("owner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    employees = []
    docs = db.collection("employees").where("company_id", "==", company_id).stream()
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        # Omite empleados dados de baja: no se les registra novedades ni finiquito.
        if not data.get("active", True):
            continue
        employees.append(Employee(**data))
    return employees


def _owned_employee_or_403(employee_id: str, user):
    """Carga un empleado y verifica que el usuario sea dueño de su empresa.

    Devuelve (doc_ref, data). Lanza 404 si no existe, 403 si no es del dueño.
    """
    doc_ref = db.collection("employees").document(employee_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Employee not found")
    data = doc.to_dict()
    company_doc = db.collection("companies").document(data["company_id"]).get()
    if not company_doc.exists or company_doc.to_dict().get("owner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return doc_ref, data


@router.get("/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str, user=Depends(get_current_user)):
    _, data = _owned_employee_or_403(employee_id, user)
    data["id"] = employee_id
    return Employee(**data)


@router.put("/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, employee: Employee, user=Depends(get_current_user)):
    doc_ref, existing = _owned_employee_or_403(employee_id, user)

    employee_data = employee.dict(exclude={"id"})
    # El empleado queda atado a su empresa original: no se permite reasignarlo
    # a otra empresa vía edición.
    employee_data["company_id"] = existing["company_id"]
    doc_ref.set(employee_data)

    employee.id = employee_id
    employee.company_id = existing["company_id"]
    return employee
