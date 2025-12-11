from pathlib import Path

from pipeline.markdown_loader import iter_markdown


def test_iter_markdown_parses_front_matter(tmp_path: Path):
    root = tmp_path / "profile"
    root.mkdir()
    md = root / "doc.md"
    md.write_text(
        """---
type: job
id: job_1
title: Engineer
---
Body text here.
        """,
        encoding="utf8",
    )

    docs = list(iter_markdown(root))
    assert len(docs) == 1
    d = docs[0]
    assert d.path == md
    assert d.metadata["type"] == "job"
    assert d.metadata["id"] == "job_1"
    assert "Body text here" in d.body


def test_iter_markdown_no_front_matter(tmp_path: Path):
    root = tmp_path / "docs"
    root.mkdir()
    md = root / "note.md"
    md.write_text("Just text", encoding="utf8")

    docs = list(iter_markdown(root))
    assert len(docs) == 1
    assert docs[0].metadata == {}
    assert docs[0].body == "Just text"


def test_iter_markdown_missing_root(tmp_path: Path):
    missing = tmp_path / "does_not_exist"
    # Should yield nothing and not crash
    docs = list(iter_markdown(missing))
    assert docs == []
