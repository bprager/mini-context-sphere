from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .ai_client import build_backend
from .config import load_config
from .hypergraph_writer import HypergraphWriter, Node
from .markdown_loader import iter_markdown
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
        cmd_init_from_markdown(args)
    elif args.command == "update-from-markdown":
        cmd_update_from_markdown(args)
    elif args.command == "export-sqlite":
        cmd_export_sqlite()
    else:
        parser.error(f"Unknown command {args.command!r}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hypergraph pipeline CLI (stub implementation).")
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser(
        "init-from-markdown",
        help="Initialize hypergraph from markdown for the configured profile.",
    )
    p_init.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the hypergraph database from scratch (deletes existing db file).",
    )
    p_init.add_argument(
        "--append",
        action="store_true",
        help="Append/update into the existing hypergraph (default).",
    )

    p_upd = subparsers.add_parser(
        "update-from-markdown",
        help="Update existing hypergraph from markdown for the configured profile.",
    )
    p_upd.add_argument(
        "--append",
        action="store_true",
        help="Append/update into the existing hypergraph (default).",
    )

    subparsers.add_parser(
        "export-sqlite",
        help="Export a runtime SQLite snapshot for the backend.",
    )

    return parser


def cmd_init_from_markdown(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = argparse.Namespace(rebuild=False, append=True)
    cfg = load_config()
    logger.info(
        "init_from_markdown_start",
        extra={
            "hypergraph_db_path": str(cfg.hypergraph_db_path),
            "markdown_root": str(cfg.markdown_root),
            "profile_name": cfg.profile_name,
        },
    )

    # Rebuild: remove existing db file for a clean slate
    if getattr(args, "rebuild", False) and cfg.hypergraph_db_path.exists():
        try:
            cfg.hypergraph_db_path.unlink()
            logger.info("rebuild_db_removed", extra={"path": str(cfg.hypergraph_db_path)})
        except OSError:
            logger.exception("rebuild_db_remove_failed")

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
    # Use build_mode for faster bulk ingestion, then finalize FTS
    with HypergraphWriter(cfg.hypergraph_db_path, build_mode=True) as writer:
        for doc in docs:
            node_id = doc.metadata.get("id") or doc.path.stem
            # if the doc has a type, use it, otherwise fall back to "Document"
            node_type = doc.metadata.get("type") or "Document"
            node = Node(id=node_id, type=node_type, data=doc.metadata)
            writer.upsert_node(node)
        # Prepare FTS for fast text search at runtime
        writer.finalize_fts()
        logger.info("init_from_markdown_done", extra={"nodes": len(docs)})

    # backend.complete is not used yet, but it is built so the interface is tested.
    _ = backend


def cmd_update_from_markdown(args: argparse.Namespace | None = None) -> None:
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
    # Force append semantics on update
    if args is None:
        args = argparse.Namespace(rebuild=False, append=True)
    else:
        args.rebuild = False
    cmd_init_from_markdown(args)
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
