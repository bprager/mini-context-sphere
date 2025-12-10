# Infra: Terraform, Cloud Run and Cloud Storage

This document describes the infrastructure for the Serverless FastMCP Starter. It expands on the infra parts of the root README.

The goal is a small, repeatable Terraform setup that creates

* one Cloud Run v2 service for the backend
* one public bucket for the static site
* minimal IAM so both are reachable for demo use

---

## Layout

Infra lives in the `infra/` folder

```text
infra/
  main.tf        Terraform resources
  variables.tf   Input variables
  outputs.tf     Useful URLs
```

---

## Variables

`variables.tf` defines the inputs that control the deployment

```hcl
variable "project_id" {
  description = "GCP project id"
}

variable "region" {
  description = "GCP region"
  default     = "us-central1"
}

variable "static_site_bucket_name" {
  description = "Name for the static site bucket"
  default     = "my-static-site"
}

variable "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  default     = "mcp-api"
}

variable "container_image" {
  description = "Full container image, for example gcr.io/PROJECT_ID/mcp-image"
}
```

You must always set

* `project_id`
* `container_image`

You can use the defaults for the rest when starting.

---

## Resources that Terraform creates

### Provider and backend

`main.tf` configures the Google provider

```hcl
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
```

Change `version` if you need a different provider version.

### Static site bucket

```hcl
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
```

Key points

* bucket name is an input variable, so you can make it match a future domain
* `website` block tells GCS which file is the main page and what to serve for 404
* IAM member uses `allUsers` with `roles/storage.objectViewer`, which makes the bucket public for demo use

You can later tighten this by removing the public member and putting a CDN or load balancer in front.

### Cloud Run v2 service

```hcl
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
```

Key points

* service image is passed in as `var.container_image`
* `min_instance_count = 0` means you only pay when there are requests
* `INGRESS_TRAFFIC_ALL` and the `public_invoker` IAM member make the service publicly reachable

You can later replace public invoker with IAM based auth.

### Outputs

`outputs.tf` provides URLs that are easy to copy

```hcl
output "static_site_url" {
  value       = "https://storage.googleapis.com/${google_storage_bucket.static_site.name}/index.html"
  description = "Entry point of the static site"
}

output "cloud_run_url" {
  value       = google_cloud_run_v2_service.mcp_api.uri
  description = "Public URL of the backend service"
}
```

After `terraform apply` these appear in the console and you can click or copy them.

---

## Observability

The starter keeps observability simple and relies on Cloud Run features.

Out of the box you get

* request logs and container stdout or stderr in Cloud Logging
* basic metrics in Cloud Monitoring (request count, latency, errors, CPU, memory)

The application adds

* structured logs from the `mcp` logger in `app/main.py` and database helpers
* INFO logs for key events, for example `mcp_query_start`, `mcp_query_ok`, `db_query`
* error logs with `logger.exception` when requests fail
* simple business fields like `result_count` and `elapsed_ms` in `extra`

You can use Cloud Logging filters to inspect these logs and create basic dashboards in Cloud Monitoring without extra libraries.

If you need deeper tracing in a future version, add OpenTelemetry and export to Cloud Trace. That is intentionally out of scope for this starter.

---

## Prerequisites

You need

* a GCP project with billing enabled
* `gcloud` CLI configured with an account that has enough rights
* Terraform installed

You also need a container image built from the project Dockerfile, for example

```bash
export PROJECT_ID="your-project-id"
gcloud builds submit --tag gcr.io/$PROJECT_ID/mcp-image
```

This uses Cloud Build to build the image and push it to Container Registry or Artifact Registry, depending on your project setup.

---

## First deployment

From the repo root

```bash
export PROJECT_ID="your-project-id"
export IMAGE="gcr.io/$PROJECT_ID/mcp-image"

cd infra
terraform init

terraform apply \
  -var "project_id=$PROJECT_ID" \
  -var "container_image=$IMAGE"
```

Terraform will show a plan. Confirm and wait until the apply finishes.

You will then see values for

* `static_site_url`
* `cloud_run_url`

---

## Updating the backend

When you change backend code

1. Build a new image

   ```bash
   export PROJECT_ID="your-project-id"
   gcloud builds submit --tag gcr.io/$PROJECT_ID/mcp-image
   ```

2. Apply a minimal Terraform update

   ```bash
   cd infra
   terraform apply \
     -var "project_id=$PROJECT_ID" \
     -var "container_image=gcr.io/$PROJECT_ID/mcp-image"
   ```

Terraform will detect that the service image changed and update the Cloud Run service.

---

## Uploading or updating the static site

After the bucket exists, sync the `static-site` directory to it

```bash
export BUCKET_NAME="my-static-site"  # or your custom name

gsutil rsync -r static-site/ gs://$BUCKET_NAME
```

This uploads new files and deletes old ones that no longer exist locally.

To see the site, use the `static_site_url` output or build the URL yourself as

```text
https://storage.googleapis.com/<bucket-name>/index.html
```

---

## Domains and production hardening

The current setup is tuned for low friction and free tier use

* public Cloud Run service
* public static bucket
* no custom domain yet

When you are ready to harden the setup

* add a load balancer and CDN in front of the bucket
* map a domain to the Cloud Run service
* remove the `allUsers` members and switch to IAM based access where needed

Those changes can live in additional Terraform files in the same `infra/` folder or in a dedicated `infra/production` tree, depending on how far you want to take this starter.

<!-- :contentReference[oaicite:1]{index=1} -->

