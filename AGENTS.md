# Development Guidelines for Payroll Ecuador

## Coding Standards
- **Backend:** Follow PEP 8 for Python. Use FastAPI for all API endpoints.
- **Frontend:** Use Functional Components with React and TypeScript. Material UI is the preferred design system.
- **I18n:** All user-facing strings must be added to `frontend/src/locales/es.json` and used via `t()` from `react-i18next`.

## Payroll Logic
- The core payroll engine is in `backend/app/services/payroll_engine.py`.
- Any change to calculation logic MUST be accompanied by a unit test in `backend/tests/`.
- Constants for IESS, SBU, etc., should be updated annually.

## Deployment
- The app is designed for Google Cloud Run.
- Database: Google Cloud Firestore.
- Auth: Firebase Authentication.

## AI Integration
- Use Vertex AI / Gemini for document processing.
- Prompts should be kept in the backend logic.
