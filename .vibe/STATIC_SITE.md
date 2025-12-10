# Static site

Single page that:
- lets user enter a query
- calls backend /mcp/query
- renders results list

Backend URL is a config constant so it can be changed per environment.

Frontend calls the HTTP JSON facade, not the gRPC endpoint directly.

