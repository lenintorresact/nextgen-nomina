from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class Region(str, Enum):
    SIERRA = "Sierra"
    AMAZONIA = "Amazonia"
    COSTA = "Costa"
    INSULAR = "Insular"

class ContractType(str, Enum):
    INDEFINITE = "Indefinido"
    FIXED_TERM = "Plazo Fijo"
    EVENTUAL = "Eventual"

class Company(BaseModel):
    id: Optional[str] = None
    ruc: str
    name: str
    region: Region
    owner_id: str

class Employee(BaseModel):
    id: Optional[str] = None
    company_id: str
    cedula: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    salary: float
    start_date: datetime
    contract_type: ContractType
    region_override: Optional[Region] = None
    accumulate_13th: bool = True
    accumulate_14th: bool = True
    accumulate_reserve_funds: bool = True

class EventType(str, Enum):
    OVERTIME_50 = "Overtime 50%"
    OVERTIME_100 = "Overtime 100%"
    COMMISSION = "Commission"
    BONUS = "Bonus"
    DEDUCTION = "Deduction"
    SALARY_CHANGE = "Salary Change"

class PayrollEvent(BaseModel):
    id: Optional[str] = None
    employee_id: str
    company_id: str
    type: EventType
    amount: float
    description: str
    date: datetime

class PayrollSlip(BaseModel):
    id: Optional[str] = None
    employee_id: str
    company_id: str
    period: str  # YYYY-MM
    base_salary: float
    earnings: Dict[str, float]
    deductions: Dict[str, float]
    net_salary: float
    iess_employee: float
    iess_employer: float
    thirteenth_salary: float
    fourteenth_salary: float
    reserve_funds: float
    vacation_provision: float
    status: str = "draft" # draft, closed
