output "artifact_registry_repo" {
  value = google_artifact_registry_repository.payroll_repo.name
}

output "service_account_email" {
  value = google_service_account.github_actions.email
}

output "firestore_name" {
  value = google_firestore_database.database.name
}
