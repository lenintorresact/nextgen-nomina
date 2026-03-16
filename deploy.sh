#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
BACKEND_SERVICE_NAME="payroll-backend"
FRONTEND_SERVICE_NAME="payroll-frontend"

echo "Using Project ID: $PROJECT_ID"

# 1. Build and Deploy Backend
echo "Deploying Backend to Cloud Run..."
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME
gcloud run deploy $BACKEND_SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo "Backend deployed at: $BACKEND_URL"

# 2. Build and Deploy Frontend
echo "Deploying Frontend to Cloud Run..."
cd ../frontend

# Create .env for frontend build
echo "VITE_API_URL=$BACKEND_URL" > .env.production

# Build the frontend (Assuming a multi-stage Dockerfile or simple Nginx setup)
# For simplicity, we will assume a basic Dockerfile for the frontend in this example
cat <<EOF > Dockerfile
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

gcloud builds submit --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME
gcloud run deploy $FRONTEND_SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated

FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo "Frontend deployed at: $FRONTEND_URL"

echo "--------------------------------------------------"
echo "Deployment Complete!"
echo "Backend: $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo "--------------------------------------------------"
