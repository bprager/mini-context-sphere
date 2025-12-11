import pipeline.schema_loader as S
import pytest
from pipeline.schema_loader import load_schema


def test_load_schema_default(monkeypatch, tmp_path):
    # Ensure default path does not exist
    monkeypatch.delenv("SCHEMA_PATH", raising=False)
    # was: default_path = Path("config") / "graph_schema.yaml"
    # Use tmp working dir where config/ is missing
    # We cannot chdir here, so rely on the file not existing in tmp repo context

    schema = load_schema(schema_path=tmp_path / "not_there.yaml")
    assert schema.name
    assert schema.entities
    labels = {e.label for e in schema.entities}
    assert "Document" in labels or "Person" in labels


def test_load_schema_env_path(monkeypatch, tmp_path):
    cfg = tmp_path / "env_schema.yaml"
    cfg.write_text(
        """
meta:
  name: from_env
entities:
  - label: Y
    pk: [id]
        """,
        encoding="utf8",
    )
    monkeypatch.setenv("SCHEMA_PATH", str(cfg))
    schema = load_schema()
    assert schema.name == "from_env"


@pytest.mark.skipif(getattr(S, "yaml", None) is None, reason="PyYAML not installed")
def test_load_schema_from_file(tmp_path):
    cfg = tmp_path / "graph.yaml"
    cfg.write_text(
        """
meta:
  name: my_graph
  version: "1.0"
  description: test schema
entities:
  - label: X
    pk: [id]
    examples: [ex]
        """,
        encoding="utf8",
    )
    schema = load_schema(schema_path=cfg)
    assert schema.name == "my_graph"
    assert [e.label for e in schema.entities] == ["X"]
