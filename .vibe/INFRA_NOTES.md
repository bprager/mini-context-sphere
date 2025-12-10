# Infra notes for AI assistants

Goal: very small, repeatable infra on GCP for a static site plus FastAPI plus gRPC MCP backend with SQLite, plus minimal observability.

## Core resources

- Cloud Run v2 service for backend
- Google Cloud Storage bucket for static site
- IAM so both are public for demo use
- Terraform lives in infra/ (main.tf, variables.tf, outputs.tf)

Design assumptions

- Single Cloud Run service, HTTP 1.1 JSON facade and gRPC MCP handler in the same container
- SQLite file is baked into the image at app/db/data.db
- No custom domain or load balancer in the starter, those come later

## Observability

Keep observability minimal

- Rely on Cloud Run logging and metrics for requests, errors, CPU and memory
- App logs use Python logging, logger name "mcp"
- Log at INFO for key events (mcp_query_start, mcp_query_ok, db_query) and at ERROR with logger.exception on failures
- Log light business metrics via structured logging (result_count, db_time_ms) instead of wiring a metrics SDK
- Health endpoint /health returns at least { "status": "ok", "version": "<string>" }

No OpenTelemetry or Cloud Trace in the starter. If deeper tracing is needed, add OTel and Cloud Trace export later and document that in docs/infra.md.

