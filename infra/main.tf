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

# Cloud Storage bucket for static files or artifacts
resource "google_storage_bucket" "context_bucket" {
  name          = "${var.project_id}-context-sphere"
  location      = var.region
  force_destroy = false  # Set to true only in non-production environments
  
  uniform_bucket_level_access = true
  
  # Lifecycle rule: Delete objects older than 30 days
  # Adjust or remove this in production based on your data retention needs
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Cloud Run service v2
resource "google_cloud_run_v2_service" "context_service" {
  name     = "mini-context-sphere"
  location = var.region
  
  template {
    containers {
      image = var.image
      
      ports {
        container_port = 8080
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      
      # Environment variables if needed
      env {
        name  = "PORT"
        value = "8080"
      }
    }
    
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Make Cloud Run service public
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = google_cloud_run_v2_service.context_service.name
  location = google_cloud_run_v2_service.context_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
