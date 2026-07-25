"""Unit tests for the OpenRouter AI provider (no network required)."""

from app.services import ai_service


def test_openrouter_not_in_chain_without_key(app):
    with app.app_context():
        app.config["OPENROUTER_API_KEY"] = None
        assert "openrouter" not in ai_service._configured_providers()


def test_openrouter_is_primary_when_configured(app):
    with app.app_context():
        app.config["AI_PRIMARY_PROVIDER"] = "openrouter"
        app.config["OPENROUTER_API_KEY"] = "or-test"
        app.config["NVIDIA_API_KEY"] = None
        app.config["ANTHROPIC_API_KEY"] = None
        app.config["OPENAI_API_KEY"] = None
        app.config["GOOGLE_API_KEY"] = None
        assert ai_service._configured_providers() == ["openrouter"]


def test_call_openrouter_posts_chat_completion(app, monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {"message": {"content": "  OpenRouter-generated caption.  "}}
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(
            url=url, headers=headers, json=json, timeout=timeout
        )
        return Response()

    monkeypatch.setattr("requests.post", fake_post)

    with app.app_context():
        app.config.update(
            OPENROUTER_API_KEY="or-test",
            OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
            OPENROUTER_MODEL="openrouter/auto-beta",
            OPENROUTER_SITE_URL="https://pulse.example",
            OPENROUTER_APP_NAME="Pulse Social AI",
        )
        result = ai_service._call_openrouter("Write a caption.")

    assert result == "OpenRouter-generated caption."
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer or-test"
    assert captured["headers"]["HTTP-Referer"] == "https://pulse.example"
    assert captured["headers"]["X-OpenRouter-Title"] == "Pulse Social AI"
    assert captured["json"]["model"] == "openrouter/auto-beta"
    assert captured["json"]["messages"][0]["content"] == "Write a caption."
    assert captured["json"]["stream"] is False


def test_generate_uses_openrouter_when_primary(app, monkeypatch):
    monkeypatch.setitem(
        ai_service._PROVIDER_FUNCS,
        "openrouter",
        lambda prompt: f"OPENROUTER:{prompt[:20]}",
    )
    with app.app_context():
        app.config["AI_PRIMARY_PROVIDER"] = "openrouter"
        app.config["OPENROUTER_API_KEY"] = "or-test"
        app.config["NVIDIA_API_KEY"] = None
        app.config["ANTHROPIC_API_KEY"] = None
        app.config["OPENAI_API_KEY"] = None
        app.config["GOOGLE_API_KEY"] = None
        result = ai_service.generate(
            "caption", "Topic: coffee\nPlatform: instagram\nTone: fun"
        )

    assert result["provider"] == "openrouter"
    assert result["cached"] is False
    assert result["result"].startswith("OPENROUTER:")
