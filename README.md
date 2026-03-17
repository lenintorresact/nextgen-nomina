# Payroll System - Ecuador (SaaS)

This is a standalone, mobile-first payroll system designed for micro and small businesses in Ecuador.

## Features
- Automatic payroll calculation (IESS, 13th/14th salaries, etc.).
- AI-assisted employee onboarding (Gemini).
- Multi-tenant architecture on Google Cloud Firestore.
- Mobile-responsive React frontend.
- Automated CI/CD pipeline.

## Prerequisites
1.  **Google Cloud Project:** Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2.  **Firebase Project:** Enable Firebase for your Google Cloud project.
    - Enable **Authentication** (Google Sign-In).
    - Enable **Firestore Database** in Native Mode.
3.  **APIs:** Enable the following APIs: Cloud Run, Cloud Build, Artifact Registry, Vertex AI.

## Automated Deployment (GitHub Actions)

Every push to the `main` branch (or development branch) triggers a deployment to Google Cloud Run.

### Step 1: Create a Service Account
Create a Service Account in GCP with the following roles:
- Cloud Run Admin
- Storage Admin
- Artifact Registry Administrator
- Service Account User
- Cloud Build Editor

### Step 2: Configure GitHub Secrets
In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add:
- `GCP_PROJECT_ID`: Your Google Cloud Project ID.
- `GCP_SA_KEY`: The JSON key of the service account created in Step 1.

### Step 3: Artifact Registry
Create a Docker repository named `payroll` in Artifact Registry:
```bash
gcloud artifacts repositories create payroll --repository-format=docker --location=us-central1
```

## Local Development

### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. `uvicorn main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. Create `.env`: `VITE_API_URL=http://localhost:8000`
4. `npm run dev`

## Tech Stack
- **Frontend:** React + TypeScript + Material UI (MUI)
- **Backend:** Python + FastAPI
- **Database:** Google Cloud Firestore (NoSQL)
- **Auth:** Firebase Authentication
- **AI:** Google Vertex AI / Gemini
