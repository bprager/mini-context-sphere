import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# Add CORS middleware to allow frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = Path(__file__).parent / "db" / "data.db"


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with a sample table."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert some sample data if table is empty
        cursor.execute("SELECT COUNT(*) FROM context_data")
        if cursor.fetchone()[0] == 0:
            sample_data = [
                ("example_key_1", "Sample context value 1"),
                ("example_key_2", "Sample context value 2"),
                ("example_key_3", "Sample context value 3"),
            ]
            cursor.executemany(
                "INSERT INTO context_data (key, value) VALUES (?, ?)",
                sample_data
            )
        
        conn.commit()


# Initialize database on startup
init_db()


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/mcp/query")
async def mcp_query(request: QueryRequest) -> JSONResponse:
    """Query endpoint that searches the SQLite database."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Simple query - search for keys or values containing the query string
            cursor.execute("""
                SELECT id, key, value, created_at
                FROM context_data
                WHERE key LIKE ? OR value LIKE ?
                ORDER BY created_at DESC
            """, (f"%{request.query}%", f"%{request.query}%"))
            
            rows = cursor.fetchall()
            results = [
                {
                    "id": row["id"],
                    "key": row["key"],
                    "value": row["value"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
            
            return JSONResponse(content={
                "query": request.query,
                "results": results,
                "count": len(results)
            })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files for serving the frontend
static_path = Path(__file__).parent.parent / "static-site"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
