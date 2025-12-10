# AI assistants, infra notes are in .vibe/INFRA_NOTES.md

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "static_site" {
  name          = var.static_site_bucket_name
  location      = var.region
  storage_class = "STANDARD"
  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }
}

resource "google_storage_bucket_iam_member" "public" {
  bucket = google_storage_bucket.static_site.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

resource "google_cloud_run_v2_service" "mcp_api" {
  name     = var.cloud_run_service_name
  location = var.region

  template {
    containers {
      image = var.container_image
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL"
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = google_cloud_run_v2_service.mcp_api.project
  location = google_cloud_run_v2_service.mcp_api.location
  service  = google_cloud_run_v2_service.mcp_api.name

  role   = "roles/run.invoker"
  member = "allUsers"
}

