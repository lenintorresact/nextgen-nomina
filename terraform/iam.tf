# Service Account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions Deployer"
}

# Assign Roles to the Service Account
resource "google_project_iam_member" "roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/storage.admin",
    "roles/artifactregistry.admin",
    "roles/iam.serviceAccountUser",
    "roles/cloudbuild.builds.editor",
    "roles/aiplatform.user",
    "roles/datastore.user" # Required for Firestore access if needed during build/deploy
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}
