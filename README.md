# mini-context-sphere
Minimal context server (with GCP hosting)

## Overview

A FastAPI-based web application with SQLite database and static frontend, ready to deploy on Google Cloud Run.

## Features

- **FastAPI Backend**: `/health` and `/mcp/query` endpoints
- **SQLite Database**: Persistent storage for context data
- **Static Frontend**: Beautiful UI for querying the database
- **Docker Ready**: Containerized for Cloud Run deployment
- **Terraform IaC**: Infrastructure as Code for GCP resources

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

3. Access the application at http://localhost:8080

### API Endpoints

- `GET /health` - Health check endpoint
- `POST /mcp/query` - Query the database
  ```json
  {
    "query": "search term"
  }
  ```

## Docker Build

```bash
docker build -t mini-context-sphere .
docker run -p 8080:8080 mini-context-sphere
```

## GCP Deployment

### Prerequisites

- Google Cloud Project
- gcloud CLI configured
- Docker image pushed to Google Container Registry or Artifact Registry
- Terraform installed

### Deploy with Terraform

1. Navigate to the infrastructure directory:
   ```bash
   cd infra
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Create a `terraform.tfvars` file:
   ```hcl
   project_id = "your-gcp-project-id"
   region     = "us-central1"
   image      = "gcr.io/your-project/mini-context-sphere:latest"
   ```

4. Deploy:
   ```bash
   terraform plan
   terraform apply
   ```

5. Get the service URL:
   ```bash
   terraform output service_url
   ```

## Project Structure

```
.
├── app/
│   ├── main.py          # FastAPI application
│   └── db/
│       └── data.db      # SQLite database (auto-created)
├── static-site/
│   └── index.html       # Frontend UI
├── infra/
│   ├── main.tf          # Terraform main config
│   ├── variables.tf     # Terraform variables
│   └── outputs.tf       # Terraform outputs
├── Dockerfile           # Container definition
└── requirements.txt     # Python dependencies
```
