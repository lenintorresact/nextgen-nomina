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
    # Estado del ciclo de nómina (progresión lineal):
    # current_period = período abierto actual (YYYY-MM); None => mes calendario.
    # closed_periods = períodos ya cerrados.
    current_period: Optional[str] = None
    closed_periods: List[str] = Field(default_factory=list)

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
    # Datos para la retención del Impuesto a la Renta (proyección anual).
    projected_personal_expenses: float = 0.0  # Gastos personales proyectados (anuales)
    family_burdens: int = 0                    # Nº de cargas familiares
    # Carga con enfermedad catastrófica/rara/huérfana → tope de 100 canastas.
    catastrophic_illness_burden: bool = False

class EventType(str, Enum):
    OVERTIME_50 = "Overtime 50%"
    OVERTIME_100 = "Overtime 100%"
    COMMISSION = "Commission"
    BONUS = "Bonus"
    DEDUCTION = "Deduction"
    SALARY_CHANGE = "Salary Change"
    # Horas extras calculadas a partir de horas (amount = nº de horas):
    HORAS_SUPLEMENTARIAS = "Horas Suplementarias (50%)"   # recargo 50%, hasta 24:00
    HORAS_EXTRAORDINARIAS = "Horas Extraordinarias (100%)"  # recargo 100%, noche/fines/feriados
    # Descuentos estructurados:
    PRESTAMO_QUIROGRAFARIO = "Préstamo Quirografario IESS"
    PRESTAMO_HIPOTECARIO = "Préstamo Hipotecario (Biess)"
    ANTICIPO = "Anticipo de Sueldo"
    MULTA = "Multa"                  # tope 10% de la remuneración (Art. 44 CT)
    FALTA = "Falta / Atraso"         # amount = nº de horas no trabajadas


class SettlementCause(str, Enum):
    """Causa de terminación que define la indemnización en la liquidación."""
    # Despido injustificado: indemnización Art. 188 + bonificación 25% Art. 185.
    DESPIDO_INTEMPESTIVO = "Despido Intempestivo"
    # Desahucio (empleador o trabajador, con aviso): solo bonificación 25% Art. 185
    # sobre años COMPLETOS (las fracciones no cuentan para este rubro).
    DESAHUCIO_EMPLEADOR = "Desahucio por el Empleador"
    DESAHUCIO_TRABAJADOR = "Desahucio por el Trabajador"
    # Renuncia voluntaria (Art. 180): solo proporcionales, sin indemnización.
    RENUNCIA = "Renuncia Voluntaria"

class PayrollEvent(BaseModel):
    id: Optional[str] = None
    employee_id: str
    company_id: str
    type: EventType
    amount: float
    description: str
    date: datetime
    # Período (YYYY-MM) al que pertenece la novedad. Se sella con el período
    # abierto de la empresa al registrarla; en eventos antiguos (sin este campo)
    # se deriva de `date`. Esto permite que una novedad registrada tras el cierre
    # caiga en el siguiente período aunque su fecha sea del mes ya cerrado.
    period: Optional[str] = None

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
    income_tax: float = 0.0  # Retención mensual del Impuesto a la Renta
    thirteenth_salary: float
    fourteenth_salary: float
    reserve_funds: float
    vacation_provision: float
    status: str = "draft" # draft, closed
