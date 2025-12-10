AI dev assistant goal: starter for static site plus FastAPI plus SQLite on GCP. All project guidance lives in .vibe/*.md.

Create:
- app/main.py (FastAPI, /health and /mcp/query using SQLite app/db/data.db, gRPC MCP service plus HTTP JSON facade)
- static-site/index.html (form calling JSON API)
- Dockerfile for Cloud Run
- requirements.txt (use uv)
- infra/ Terraform for bucket and Cloud Run v2, public, vars project_id, region, image
- keep .vibe/STATUS.md updated

