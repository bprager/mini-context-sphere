# API spec

## HTTP JSON

POST /mcp/query
Request JSON:
{
"query": "string"
}

Response JSON:
{
"results": \[
{ "id": int, "content": string }
\]
}
Errors use { "detail": "message" } with HTTP status.

## gRPC

service McpService {
rpc Query(QueryRequest) returns (QueryResponse);
}

message QueryRequest { string query = 1; }
message QueryResponse {
repeated Result results = 1;
}
message Result { int64 id = 1; string content = 2; }
