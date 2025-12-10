variable "project_id" {}
variable "region" { default = "us-central1" }
variable "static_site_bucket_name" { default = "my-static-site" }
variable "cloud_run_service_name" { default = "mcp-api" }
variable "container_image" {}

