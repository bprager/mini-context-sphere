output "static_site_url" {
  value = "https://storage.googleapis.com/${google_storage_bucket.static_site.name}/index.html"
}

output "cloud_run_url" {
  value = google_cloud_run_v2_service.mcp_api.uri
}

