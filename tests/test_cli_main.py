import argparse
import sqlite3
from pathlib import Path

import pytest
from pipeline import cli as pipeline_cli


def test_cli_main_no_args_shows_help(capsys):
    # Should not raise and should print usage/help
    pipeline_cli.main([])
    out = capsys.readouterr().out
    assert "usage:" in out


def test_cli_main_init_and_update(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "hg.db"
    md_root = tmp_path / "knowledge"
    profile_root = md_root / "profile"
    profile_root.mkdir(parents=True)
    (profile_root / "doc.md").write_text(
        """---
type: Note
id: doc
---
body
""",
        encoding="utf8",
    )

    monkeypatch.setenv("HYPERGRAPH_DB_PATH", str(db_path))
    monkeypatch.setenv("MARKDOWN_ROOT", str(md_root))
    monkeypatch.setenv("PROFILE_NAME", "profile")

    # init
    pipeline_cli.main(["init-from-markdown"])
    # update (calls init internally in this stub)
    pipeline_cli.main(["update-from-markdown"])

    # verify nodes exist
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute("SELECT id,type FROM nodes").fetchall()]
        assert any(r["id"] == "doc" for r in rows)
    finally:
        conn.close()


def test_cli_main_export(monkeypatch, tmp_path: Path):
    # prepare existing source db
    source = tmp_path / "hg.db"
    conn = sqlite3.connect(source)
    try:
        conn.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, data TEXT)")
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setenv("HYPERGRAPH_DB_PATH", str(source))
    monkeypatch.setenv("MARKDOWN_ROOT", str(tmp_path / "knowledge"))
    monkeypatch.setenv("PROFILE_NAME", "profile")

    runtime_db = Path("app") / "db" / "data.db"
    if runtime_db.exists():
        runtime_db.unlink()

    pipeline_cli.main(["export-sqlite"])
    assert runtime_db.exists()


def test_cli_flag_content_hash_ids_sets_env(monkeypatch, capsys):
    import os

    monkeypatch.delenv("CONTENT_HASH_IDS", raising=False)
    # No command provided on purpose; should set env and print help
    pipeline_cli.main(["--content-hash-ids"])
    out = capsys.readouterr().out
    assert os.getenv("CONTENT_HASH_IDS") == "1"
    assert "usage:" in out


def test_cli_unknown_command(monkeypatch, tmp_path: Path):
    # Ensure unknown command triggers parser.error / SystemExit
    with pytest.raises(SystemExit):
        pipeline_cli.main(["does-not-exist"])


def test_cli_rebuild_unlink_error(monkeypatch, tmp_path: Path):
    # Prepare a dummy db file and simulate unlink raising OSError
    db_path = tmp_path / "hg.db"
    db_path.write_text("", encoding="utf8")
    monkeypatch.setenv("HYPERGRAPH_DB_PATH", str(db_path))
    monkeypatch.setenv("MARKDOWN_ROOT", str(tmp_path / "knowledge"))
    monkeypatch.setenv("PROFILE_NAME", "profile")

    called = {"unlink": False}

    def raise_unlink(self):  # type: ignore[no-untyped-def]
        called["unlink"] = True
        raise OSError("simulated")

    monkeypatch.setattr(Path, "unlink", raise_unlink, raising=True)

    # Should handle the exception and proceed without raising
    pipeline_cli.cmd_init_from_markdown(argparse.Namespace(rebuild=True, append=True))
    assert called["unlink"] is True


def test_cli_export_source_missing(monkeypatch, tmp_path: Path):
    # Point to a non-existent source file and confirm graceful return
    monkeypatch.setenv("HYPERGRAPH_DB_PATH", str(tmp_path / "missing.db"))
    monkeypatch.setenv("MARKDOWN_ROOT", str(tmp_path / "knowledge"))
    monkeypatch.setenv("PROFILE_NAME", "profile")
    pipeline_cli.main(["export-sqlite"])  # should not raise
