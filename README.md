# Payroll System - Ecuador (SaaS)

This is a standalone, mobile-first payroll system designed for micro and small businesses in Ecuador.

## Infrastructure as Code (Terraform)

We use Terraform to manage Google Cloud resources.

### Provisioning Infrastructure
1.  **Install Terraform:** [Download here](https://www.terraform.io/downloads).
2.  **Authenticate:** `gcloud auth application-default login`.
3.  **Initialize & Apply:**
    ```bash
    cd terraform
    terraform init
    terraform apply -var="project_id=[YOUR_PROJECT_ID]"
    ```
This will enable all required APIs, create the Firestore database, and set up the Artifact Registry.

## Automated Deployment (GitHub Actions)

Every push to the `main` branch triggers a deployment to Google Cloud Run.

### Step 1: GitHub Secrets
After running Terraform, you'll have a service account named `github-actions-deployer`. Generate a JSON key for it and add it to GitHub. Also, you must provide the Firebase credentials:
- `GCP_PROJECT_ID`: Your Google Cloud Project ID.
- `GCP_SA_KEY`: The JSON key of the service account.
- `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, etc.: Credentials from your Firebase project settings.

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
