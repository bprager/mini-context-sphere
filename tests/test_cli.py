import sqlite3
from pathlib import Path

from pipeline.cli import cmd_export_sqlite, cmd_init_from_markdown


def write_md(root: Path, name: str, type_: str = "Document") -> None:
    p = root / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"""---
type: {type_}
id: {name}
---
body
""",
        encoding="utf8",
    )


def test_cli_init_and_export(monkeypatch, tmp_path: Path):
    # Configure environment for pipeline
    db_path = tmp_path / "hypergraph.db"
    md_root = tmp_path / "knowledge"
    profile_name = "profile"
    profile_root = md_root / profile_name
    write_md(profile_root, "doc1")
    write_md(profile_root, "doc2", type_="Job")

    monkeypatch.setenv("HYPERGRAPH_DB_PATH", str(db_path))
    monkeypatch.setenv("MARKDOWN_ROOT", str(md_root))
    monkeypatch.setenv("PROFILE_NAME", profile_name)

    # Run init-from-markdown (uses HypergraphWriter to create nodes)
    cmd_init_from_markdown()

    # Ensure nodes exist
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute("SELECT id,type FROM nodes ORDER BY id").fetchall()]
        assert rows == [
            {"id": "doc1", "type": "Document"},
            {"id": "doc2", "type": "Job"},
        ]
    finally:
        conn.close()

    # Export runtime snapshot
    app_db = Path("app") / "db" / "data.db"
    if app_db.exists():
        app_db.unlink()
    cmd_export_sqlite()
    assert app_db.exists()
