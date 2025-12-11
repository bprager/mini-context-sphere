import sqlite3
from pathlib import Path

import pytest
from pipeline.cli import cmd_export_sqlite, cmd_init_from_markdown


def write_doc(root: Path, name: str, meta: dict[str, str] | None = None, body: str = "") -> None:
    meta = meta or {"type": "Document", "id": name}
    header = "---\n" + "\n".join(f"{k}: {v}" for k, v in meta.items()) + "\n---\n"
    (root / f"{name}.md").write_text(header + body, encoding="utf8")


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_end_to_end_init_and_query(monkeypatch, tmp_path: Path):
    # Prepare markdown
    md_root = tmp_path / "knowledge" / "profile"
    md_root.mkdir(parents=True)
    write_doc(
        md_root,
        "job1",
        {"type": "Job", "id": "job1", "title": "Engineer"},
        "Worked on X",
    )
    write_doc(md_root, "org1", {"type": "Organization", "id": "org1", "name": "Acme"})

    # Configure environment
    db_path = tmp_path / "hypergraph.db"
    monkeypatch.setenv("HYPERGRAPH_DB_PATH", str(db_path))
    monkeypatch.setenv("MARKDOWN_ROOT", str(tmp_path / "knowledge"))
    monkeypatch.setenv("PROFILE_NAME", "profile")

    # Run pipeline
    cmd_init_from_markdown()

    # Verify nodes
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute("SELECT id,type FROM nodes ORDER BY id")]
        ids = {r["id"] for r in rows}
        assert {"job1", "org1"}.issubset(ids)
    finally:
        conn.close()

    # Export runtime DB
    runtime_db = Path("app") / "db" / "data.db"
    if runtime_db.exists():
        runtime_db.unlink()
    cmd_export_sqlite()
    assert runtime_db.exists()
