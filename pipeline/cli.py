afrom __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import load_config
from .ai_client import build_backend
from .markdown_loader import iter_markdown
from .hypergraph_writer import HypergraphWriter, Node, Edge
from .schema_loader import load_schema  # new import

logger = logging.getLogger("pipeline.cli")


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO)
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "command") or args.command is None:
        parser.print_help()
        return

    if args.command == "init-from-markdown":
        cmd_init_from_markdown()
    elif args.command == "update-from-markdown":
        cmd_update_from_markdown()
    elif args.command == "export-sqlite":
        cmd_export_sqlite()
    else:
        parser.error(f"Unknown command {args.command!r}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hypergraph pipeline CLI (stub implementation)."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "init-from-markdown",
        help="Initialize hypergraph from markdown for the configured profile.",
    )

    subparsers.add_parser(
        "update-from-markdown",
        help="Update existing hypergraph from markdown for the configured profile.",
    )

    subparsers.add_parser(
        "export-sqlite",
        help="Export a runtime SQLite snapshot for the backend.",
    )

    return parser


def cmd_init_from_markdown() -> None:
    cfg = load_config()
    logger.info(
        "init_from_markdown_start",
        extra={
            "hypergraph_db_path": str(cfg.hypergraph_db_path),
            "markdown_root": str(cfg.markdown_root),
            "profile_name": cfg.profile_name,
        },
    )

    backend = build_backend(cfg.ai_provider, cfg.ai_model)
    profile_root = cfg.profile_root

    # load schema (generic or LinkedIn tuned, depending on SCHEMA_PATH or config)
    schema = load_schema()
    logger.info(
        "schema_in_use",
        extra={"entities": [e.label for e in schema.entities]},
    )

    docs = list(iter_markdown(profile_root))
    logger.info("markdown_documents_found", extra={"count": len(docs)})

    # Stub: just creates the DB and logs nodes that would be created.
    with HypergraphWriter(cfg.hypergraph_db_path) as writer:
        for doc in docs:
            node_id = doc.metadata.get("id") or doc.path.stem
            # if the doc has a type, use it, otherwise fall back to "Document"
            node_type = doc.metadata.get("type") or "Document"
            node = Node(id=node_id, type=node_type, data=doc.metadata)
            writer.upsert_node(node)
        logger.info("init_from_markdown_done", extra={"nodes": len(docs)})

    # backend.complete is not used yet, but it is built so the interface is tested.
    _ = backend


def cmd_update_from_markdown() -> None:
    cfg = load_config()
    logger.info(
        "update_from_markdown_start",
        extra={
            "hypergraph_db_path": str(cfg.hypergraph_db_path),
            "markdown_root": str(cfg.markdown_root),
            "profile_name": cfg.profile_name,
        },
    )

    # For now, this does the same as init and can be refined later.
    cmd_init_from_markdown()
    logger.info("update_from_markdown_done")


def cmd_export_sqlite() -> None:
    cfg = load_config()
    logger.info(
        "export_sqlite_start",
        extra={"hypergraph_db_path": str(cfg.hypergraph_db_path)},
    )

    # Stub: copy the hypergraph db into the runtime db path if it exists.
    source = cfg.hypergraph_db_path
    runtime_db = Path("app") / "db" / "data.db"

    if not source.exists():
        logger.warning("export_sqlite_source_missing", extra={"source": str(source)})
        return

    runtime_db.parent.mkdir(parents=True, exist_ok=True)
    runtime_db.write_bytes(source.read_bytes())
    logger.info(
        "export_sqlite_done",
        extra={"source": str(source), "runtime_db": str(runtime_db)},
    )


if __name__ == "__main__":
    main()

