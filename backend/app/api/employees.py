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
        employees.append(Employee(**data))
    return employees
