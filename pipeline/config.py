afrom __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline.

    Values are loaded from environment variables with safe defaults so that
    the pipeline can run locally without extra setup.
    """

    hypergraph_db_path: Path
    ai_provider: str
    ai_model: str
    markdown_root: Path
    profile_name: str

    @property
    def profile_root(self) -> Path:
        return self.markdown_root / self.profile_name


def load_config() -> PipelineConfig:
    """Load pipeline config from environment variables.

    HYPERGRAPH_DB_PATH  path to SQLite file, default "hypergraph.db"
    AI_PROVIDER         openai, gemini, ollama or none, default "none"
    AI_MODEL            model name, left empty by default
    MARKDOWN_ROOT       base markdown folder, default "knowledge"
    PROFILE_NAME        logical profile name, default "profile"
    """
    hypergraph_db_path = Path(os.getenv("HYPERGRAPH_DB_PATH", "hypergraph.db"))
    ai_provider = os.getenv("AI_PROVIDER", "none")
    ai_model = os.getenv("AI_MODEL", "")
    markdown_root = Path(os.getenv("MARKDOWN_ROOT", "knowledge"))
    profile_name = os.getenv("PROFILE_NAME", "profile")

    return PipelineConfig(
        hypergraph_db_path=hypergraph_db_path,
        ai_provider=ai_provider,
        ai_model=ai_model,
        markdown_root=markdown_root,
        profile_name=profile_name,
    )

