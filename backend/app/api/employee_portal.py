from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models.schemas import PayrollSlip
from ..core.config import db, get_current_user

router = APIRouter(prefix="/employee-portal", tags=["employee-portal"])

@router.get("/my-slips", response_model=List[PayrollSlip])
async def get_my_slips(user=Depends(get_current_user)):
    # In this system, we identify the employee by their email or cedula
    # linked to the authenticated user's email/phone.
    # For now, we search for slips where the employee's email matches the user's email.

    user_email = user.get("email")
    if not user_email:
        # Anonymous/demo users have no email; there are simply no slips for them.
        return []

    # First, find employee records associated with this email
    employee_docs = db.collection("employees").where("email", "==", user_email).stream()
    employee_ids = [doc.id for doc in employee_docs]

    if not employee_ids:
        return []

    # Then find all slips for these employee records (could be across multiple companies)
    slips = []
    # Firestore 'in' query supports up to 10 items. For a unified view:
    slips_docs = db.collection("slips").where("employee_id", "in", employee_ids).stream()

    for doc in slips_docs:
        data = doc.to_dict()
        data["id"] = doc.id
        slips.append(PayrollSlip(**data))

    return slips
