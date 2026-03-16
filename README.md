# Payroll System - Ecuador (SaaS)

This is a standalone, mobile-first payroll system designed for micro and small businesses in Ecuador.

## Prerequisites
1.  **Google Cloud Project:** Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2.  **Firebase Project:** Enable Firebase for your Google Cloud project at [Firebase Console](https://console.firebase.google.com/).
    - Enable **Authentication** (Google Sign-In).
    - Enable **Firestore Database** in Native Mode.
3.  **Google Cloud SDK:** Install and initialize the `gcloud` CLI.

## Deployment Guide (Google Cloud Run)

We have provided a `deploy.sh` script to automate the process.

### Step 1: Configuration
Update the `firebaseConfig` in `frontend/src/firebase.ts` with your actual Firebase project credentials.

### Step 2: Run Deployment Script
Ensure you are authenticated and have the correct project selected:
```bash
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]
chmod +x deploy.sh
./deploy.sh
```

### Step 3: Enable APIs
You must enable the following APIs in your Google Cloud Project:
- Cloud Run API
- Cloud Build API
- Artifact Registry API
- Vertex AI API (for document scanning)
- Firestore API

## Local Development

### Backend Setup
1. Navigate to `backend/`
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `uvicorn main:app --reload`

### Frontend Setup
1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Create a `.env` file: `VITE_API_URL=http://localhost:8000`
4. Run: `npm run dev`

## Tech Stack
- **Frontend:** React + TypeScript + Material UI (MUI)
- **Backend:** Python + FastAPI
- **Database:** Google Cloud Firestore (NoSQL)
- **Auth:** Firebase Authentication
- **AI:** Google Vertex AI / Gemini
