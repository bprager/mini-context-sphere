from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("pipeline.markdown")


@dataclass
class MarkdownDocument:
    """Simple representation of a markdown file.

    metadata  optional front matter parsed as a mapping
    body      markdown body without the front matter block
    """

    path: Path
    metadata: dict[str, Any]
    body: str


def iter_markdown(root: Path) -> Iterable[MarkdownDocument]:
    """Yield all markdown documents under a given root.

    This is intentionally simple. It supports optional front matter using the
    pattern:

    ---
    key: value
    ---
    body text...

    Anything that is not front matter is treated as body.
    """
    if not root.exists():
        logger.info("markdown_root_missing", extra={"root": str(root)})
        return

    for path in sorted(root.rglob("*.md")):
        doc = _load_single(path)
        logger.info(
            "markdown_loaded",
            extra={"path": str(path), "has_metadata": bool(doc.metadata)},
        )
        yield doc


def _load_single(path: Path) -> MarkdownDocument:
    text = path.read_text(encoding="utf8")
    metadata: dict[str, Any] = {}
    body = text

    if text.startswith("---\n"):
        # Very small and forgiving front matter parser
        parts = text.split("---", 2)
        if len(parts) >= 3:
            _, header, rest = parts[0], parts[1], parts[2]
            body = rest.lstrip("\n")
            for line in header.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

    return MarkdownDocument(path=path, metadata=metadata, body=body)
