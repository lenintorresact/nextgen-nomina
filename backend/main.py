from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import companies, employees, payroll, ai, employee_portal, demo

app = FastAPI(title="Payroll Ecuador API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # We authenticate with bearer tokens in the Authorization header, not cookies.
    # "*" origin + allow_credentials=True is an invalid combo browsers reject, so
    # credentials must stay False here.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(employees.router)
app.include_router(payroll.router)
app.include_router(ai.router)
app.include_router(employee_portal.router)
app.include_router(demo.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Payroll Ecuador API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
