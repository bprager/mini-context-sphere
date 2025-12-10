# Infra notes for AI assistants

Goal: very small, repeatable infra on GCP for a static site plus FastAPI plus gRPC MCP backend with SQLite, plus minimal observability.

Core resources:
- Cloud Run v2 service for backend
- Google Cloud Storage bucket for static site
- IAM so both are public for demo use
- Terraform lives in infra/ (main.tf, variables.tf, outputs.tf)

Design assumptions:
- Single Cloud Run service, HTTP JSON facade and gRPC MCP handler in the same container
- SQLite file with graph extension is baked into the image at app/db/data.db
- No custom domain or load balancer in the starter, those come later

Observability:
- use Cloud Run logging and metrics, plus the "mcp" logger inside the app
- log key events (mcp_query_start, mcp_query_ok, db_query) and basic metrics (result_count, db_time_ms)
- keep instrumentation light, no OpenTelemetry in the starter

