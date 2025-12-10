output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.context_service.uri
}

output "bucket_name" {
  description = "Name of the Cloud Storage bucket"
  value       = google_storage_bucket.context_bucket.name
}

output "bucket_url" {
  description = "URL of the Cloud Storage bucket"
  value       = google_storage_bucket.context_bucket.url
}
