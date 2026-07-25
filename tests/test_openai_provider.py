"""Unit tests for the OpenAI content-generation provider (no network required)."""

import sys
import types

from app.services import ai_service


def test_openai_is_primary_when_configured(app):
    with app.app_context():
        app.config.update(
            AI_PRIMARY_PROVIDER="openai",
            OPENAI_API_KEY="test-openai-key",
            ANTHROPIC_API_KEY=None,
            NVIDIA_API_KEY=None,
            OPENROUTER_API_KEY=None,
            GOOGLE_API_KEY=None,
        )
        assert ai_service._configured_providers() == ["openai"]


def test_call_openai_uses_configured_model_and_returns_text(app, monkeypatch):
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(output_text="  OpenAI-generated caption.  ")

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["api_key"] = kwargs["api_key"]
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))

    with app.app_context():
        app.config.update(OPENAI_API_KEY="test-openai-key", OPENAI_MODEL="gpt-4o-mini")
        result = ai_service._call_openai("Write a caption.")

    assert result == "OpenAI-generated caption."
    assert captured == {
        "api_key": "test-openai-key",
        "model": "gpt-4o-mini",
        "input": "Write a caption.",
        "max_output_tokens": 2000,
    }