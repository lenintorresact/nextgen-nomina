from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models.schemas import Company
from ..core.config import db, get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])

@router.post("/", response_model=Company)
async def create_company(company: Company, user=Depends(get_current_user)):
    company_data = company.dict(exclude={"id"})
    company_data["owner_id"] = user["uid"]

    doc_ref = db.collection("companies").document()
    doc_ref.set(company_data)

    company.id = doc_ref.id
    return company

@router.get("/", response_model=List[Company])
async def get_companies(user=Depends(get_current_user)):
    companies = []
    docs = db.collection("companies").where("owner_id", "==", user["uid"]).stream()
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        companies.append(Company(**data))
    return companies
