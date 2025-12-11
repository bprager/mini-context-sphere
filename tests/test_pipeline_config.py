from pathlib import Path

from pipeline.config import load_config


def test_load_config_defaults(monkeypatch):
    # Clear env
    monkeypatch.delenv("HYPERGRAPH_DB_PATH", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.delenv("MARKDOWN_ROOT", raising=False)
    monkeypatch.delenv("PROFILE_NAME", raising=False)

    cfg = load_config()
    assert cfg.hypergraph_db_path == Path("hypergraph.db")
    assert cfg.ai_provider == "none"
    assert cfg.ai_model == ""
    assert cfg.markdown_root == Path("knowledge")
    assert cfg.profile_name == "profile"


def test_load_config_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HYPERGRAPH_DB_PATH", str(tmp_path / "graph.db"))
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("MARKDOWN_ROOT", str(tmp_path / "md"))
    monkeypatch.setenv("PROFILE_NAME", "me")

    cfg = load_config()
    assert cfg.hypergraph_db_path == tmp_path / "graph.db"
    assert cfg.ai_provider == "openai"
    assert cfg.ai_model == "gpt-4o-mini"
    assert cfg.markdown_root == tmp_path / "md"
    assert cfg.profile_name == "me"
