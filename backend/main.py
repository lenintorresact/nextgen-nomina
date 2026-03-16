from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .app.api import companies, employees, payroll, ai

app = FastAPI(title="Payroll Ecuador API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(employees.router)
app.include_router(payroll.router)
app.include_router(ai.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Payroll Ecuador API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
