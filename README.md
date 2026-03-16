# Payroll System - Ecuador (SaaS)

This is a standalone, mobile-first payroll system designed for micro and small businesses in Ecuador.

## Features
- Automatic payroll calculation based on events.
- Ecuadorian labor law compliance (IESS, 13th/14th salaries, Reserve Funds, etc.).
- AI-assisted employee onboarding (using Gemini).
- Self-service portal for employees.
- Multi-tenant SaaS architecture.

## Tech Stack
- **Frontend:** React + TypeScript + Material UI (MUI)
- **Backend:** Python + FastAPI
- **Database:** Google Cloud Firestore (NoSQL)
- **Auth:** Firebase Authentication
- **AI:** Google Vertex AI / Gemini

## Project Structure
- `/backend`: FastAPI application, payroll engine, and API logic.
- `/frontend`: React application with Material UI.

## Getting Started

### Backend Setup
1. Navigate to `backend/`
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the server: `uvicorn main:app --reload --port 8000`

### Frontend Setup
1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`

## Deployment
This project is designed to be deployed to **Google Cloud Run**.
- Backend service: Build and deploy the Dockerfile in `backend/`.
- Frontend service: Build the production assets and deploy (e.g., using a simple Nginx Dockerfile or Firebase Hosting).
