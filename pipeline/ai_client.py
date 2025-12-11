from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger("pipeline.ai")


class AiBackend(Protocol):
    """Minimal AI backend interface."""

    def complete(self, prompt: str) -> str:
        """Return a completion for the given prompt."""
        ...


class NoopBackend:
    """Fallback backend that raises if used."""

    def complete(self, prompt: str) -> str:
        raise RuntimeError("No AI backend configured, set AI_PROVIDER and AI_MODEL")


class OpenAiBackend:
    """Stub for an OpenAI based backend."""

    def __init__(self, model: str) -> None:
        self.model = model

    def complete(self, prompt: str) -> str:  # pragma: no cover - stub
        raise NotImplementedError(
            "OpenAiBackend.complete is not implemented yet. "
            "Wire this to the OpenAI SDK or your own client."
        )


class GeminiBackend:
    """Stub for a Gemini based backend."""

    def __init__(self, model: str) -> None:
        self.model = model

    def complete(self, prompt: str) -> str:  # pragma: no cover - stub
        raise NotImplementedError(
            "GeminiBackend.complete is not implemented yet. "
            "Wire this to the Gemini SDK or your own client."
        )


class OllamaBackend:
    """Stub for a local Ollama based backend."""

    def __init__(self, model: str) -> None:
        self.model = model

    def complete(self, prompt: str) -> str:  # pragma: no cover - stub
        raise NotImplementedError(
            "OllamaBackend.complete is not implemented yet. Wire this to your Ollama client."
        )


def build_backend(provider: str, model: str) -> AiBackend:
    """Return an AI backend instance for the given provider name.

    Provider names are case insensitive. If provider is "none" or empty,
    a NoopBackend is returned and any call to complete will raise.
    """
    provider_norm = (provider or "").strip().lower()
    logger.info("build_backend", extra={"provider": provider_norm, "model": model})

    if provider_norm in {"", "none"}:
        return NoopBackend()
    if provider_norm == "openai":
        return OpenAiBackend(model=model)
    if provider_norm == "gemini":
        return GeminiBackend(model=model)
    if provider_norm == "ollama":
        return OllamaBackend(model=model)

    logger.warning("unknown_ai_provider", extra={"provider": provider})
    return NoopBackend()
