from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("pipeline.schema")

try:
    import yaml  # type: ignore[import]
except Exception:
    yaml = None  # type: ignore[assignment]


@dataclass
class EntitySchema:
    label: str
    pk: list[str]
    examples: list[str]


@dataclass
class GraphSchema:
    name: str
    version: str
    description: str
    entities: list[EntitySchema]


def _default_schema() -> GraphSchema:
    """Fallback schema used when no YAML is available.

    Keep this very small and neutral. Users and tutorials can override it
    with config/graph_schema.yaml or SCHEMA_PATH.
    """
    return GraphSchema(
        name="default_graph",
        version="1.0",
        description="Generic schema for nodes derived from markdown documents.",
        entities=[
            EntitySchema(
                label="Document",
                pk=["id"],
                examples=["generic_markdown_doc"],
            ),
            EntitySchema(
                label="Person",
                pk=["name"],
                examples=["Example Person"],
            ),
            EntitySchema(
                label="Organization",
                pk=["name"],
                examples=["Example Org"],
            ),
            EntitySchema(
                label="Skill",
                pk=["name"],
                examples=["Python", "Cloud"],
            ),
        ],
    )


def load_schema(schema_path: Path | None = None) -> GraphSchema:
    """Load a graph schema from YAML or fall back to a default schema.

    Resolution order:
    1) explicit schema_path argument
    2) SCHEMA_PATH environment variable
    3) config/graph_schema.yaml if it exists
    4) built in default schema
    """
    if schema_path is None:
        env_path = os.getenv("SCHEMA_PATH")
        if env_path:
            schema_path = Path(env_path)
        else:
            schema_path = Path("config") / "graph_schema.yaml"

    if not schema_path.exists():
        logger.info(
            "schema_file_missing",
            extra={"schema_path": str(schema_path)},
        )
        schema = _default_schema()
        logger.info(
            "schema_default_used",
            extra={"entities": [e.label for e in schema.entities]},
        )
        return schema

    if yaml is None:
        logger.warning(
            "pyyaml_missing_default_schema_used",
            extra={"schema_path": str(schema_path)},
        )
        return _default_schema()

    data = yaml.safe_load(schema_path.read_text(encoding="utf8")) or {}
    meta = data.get("meta", {}) or {}
    entities_raw = data.get("entities", []) or []

    entities: list[EntitySchema] = []
    for item in entities_raw:
        label = str(item.get("label", "Unknown"))
        pk = [str(v) for v in item.get("pk", [])]
        examples = [str(v) for v in item.get("examples", [])]
        entities.append(EntitySchema(label=label, pk=pk, examples=examples))

    schema = GraphSchema(
        name=str(meta.get("name", "graph")),
        version=str(meta.get("version", "1.0")),
        description=str(meta.get("description", "")),
        entities=entities,
    )

    logger.info(
        "schema_loaded",
        extra={
            "schema_path": str(schema_path),
            "name": schema.name,
            "version": schema.version,
            "entities": [e.label for e in schema.entities],
        },
    )
    return schema
