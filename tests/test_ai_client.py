import pytest
from pipeline.ai_client import (
    GeminiBackend,
    NoopBackend,
    OllamaBackend,
    OpenAiBackend,
    build_backend,
)


def test_build_backend_noop():
    b = build_backend("none", "")
    assert isinstance(b, NoopBackend)
    with pytest.raises(RuntimeError):
        b.complete("hi")


def test_build_backend_openai():
    b = build_backend("openai", "gpt-4o-mini")
    assert isinstance(b, OpenAiBackend)


def test_build_backend_gemini():
    b = build_backend("gemini", "gemini-1.5-pro")
    assert isinstance(b, GeminiBackend)


def test_build_backend_ollama():
    b = build_backend("ollama", "llama3")
    assert isinstance(b, OllamaBackend)


def test_build_backend_unknown_provider():
    # Unknown providers fall back to NoopBackend
    b = build_backend("mystery", "")
    assert isinstance(b, NoopBackend)
