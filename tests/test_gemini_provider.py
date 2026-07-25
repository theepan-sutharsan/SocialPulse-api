"""Unit tests for the Gemini AI provider (no network required)."""

from app.services import ai_service


def test_gemini_not_in_chain_without_key(app):
    with app.app_context():
        app.config["GOOGLE_API_KEY"] = None
        assert "gemini" not in ai_service._configured_providers()


def test_gemini_is_primary_when_configured(app):
    with app.app_context():
        app.config["AI_PRIMARY_PROVIDER"] = "gemini"
        app.config["GOOGLE_API_KEY"] = "test-gemini-key"
        app.config["NVIDIA_API_KEY"] = None
        app.config["OPENROUTER_API_KEY"] = None
        app.config["ANTHROPIC_API_KEY"] = None
        app.config["OPENAI_API_KEY"] = None
        assert ai_service._configured_providers() == ["gemini"]


def test_call_gemini_posts_generate_content(app, monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "  Gemini caption here.  "}]
                        }
                    }
                ]
            }

    def fake_post(url, params=None, headers=None, json=None, timeout=None):
        captured.update(
            url=url, params=params, headers=headers, json=json, timeout=timeout
        )
        return Response()

    monkeypatch.setattr("requests.post", fake_post)

    with app.app_context():
        app.config.update(
            GOOGLE_API_KEY="test-gemini-key",
            GEMINI_BASE_URL="https://generativelanguage.googleapis.com/v1beta",
            GEMINI_MODEL="gemini-2.0-flash",
        )
        text = ai_service._call_gemini("Write a caption.")

    assert text == "Gemini caption here."
    assert (
        captured["url"]
        == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    )
    assert captured["headers"]["X-goog-api-key"] == "test-gemini-key"
    assert captured["json"]["contents"][0]["parts"][0]["text"] == "Write a caption."
    assert captured["json"]["generationConfig"]["maxOutputTokens"] == 2000


def test_generate_uses_gemini_when_primary(app, monkeypatch):
    monkeypatch.setitem(
        ai_service._PROVIDER_FUNCS,
        "gemini",
        lambda prompt: f"GEMINI:{prompt[:20]}",
    )
    with app.app_context():
        app.config["AI_PRIMARY_PROVIDER"] = "gemini"
        app.config["GOOGLE_API_KEY"] = "test-gemini-key"
        app.config["NVIDIA_API_KEY"] = None
        app.config["OPENROUTER_API_KEY"] = None
        app.config["ANTHROPIC_API_KEY"] = None
        app.config["OPENAI_API_KEY"] = None
        result = ai_service.generate(
            "caption", "Topic: coffee\nPlatform: instagram\nTone: fun"
        )

    assert result["provider"] == "gemini"
    assert result["cached"] is False
    assert result["result"].startswith("GEMINI:")
