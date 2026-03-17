terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable Required APIs
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "firebase.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# Artifact Registry for Docker Images
resource "google_artifact_registry_repository" "payroll_repo" {
  location      = var.region
  repository_id = "payroll"
  description   = "Docker repository for Payroll SaaS"
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}

# Firestore Database (Native Mode)
resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_project_service.services]
}
