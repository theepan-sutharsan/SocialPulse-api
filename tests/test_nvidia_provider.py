"""Unit tests for the NVIDIA NIM AI provider (no network required)."""

from app.services import ai_service


def test_nvidia_not_in_chain_without_key(app):
    with app.app_context():
        app.config["NVIDIA_API_KEY"] = None
        assert "nvidia" not in ai_service._configured_providers()


def test_nvidia_is_primary_when_configured(app):
    with app.app_context():
        app.config["AI_PRIMARY_PROVIDER"] = "nvidia"
        app.config["NVIDIA_API_KEY"] = "nvapi-test"
        app.config["ANTHROPIC_API_KEY"] = None
        app.config["OPENAI_API_KEY"] = None
        app.config["GOOGLE_API_KEY"] = None
        providers = ai_service._configured_providers()
        assert providers[0] == "nvidia"


def test_call_nvidia_posts_chat_completions(app, monkeypatch):
    captured = {}

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {"message": {"content": "  A scroll-stopping caption.  "}}
                ]
            }

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _Resp()

    monkeypatch.setattr("requests.post", _fake_post)

    with app.app_context():
        app.config["NVIDIA_API_KEY"] = "nvapi-test"
        app.config["NVIDIA_BASE_URL"] = "https://integrate.api.nvidia.com/v1"
        app.config["NVIDIA_MODEL"] = "google/diffusiongemma-26b-a4b-it"
        text = ai_service._call_nvidia("Write a caption about coffee.")

    assert text == "A scroll-stopping caption."
    assert captured["url"] == "https://integrate.api.nvidia.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer nvapi-test"
    assert captured["json"]["model"] == "google/diffusiongemma-26b-a4b-it"
    assert captured["json"]["messages"][0]["content"] == "Write a caption about coffee."
    assert captured["json"]["stream"] is False


def test_generate_uses_nvidia_when_primary(app, monkeypatch):
    monkeypatch.setitem(
        ai_service._PROVIDER_FUNCS,
        "nvidia",
        lambda prompt: f"NVIDIA:{prompt[:20]}",
    )
    with app.app_context():
        app.config["AI_PRIMARY_PROVIDER"] = "nvidia"
        app.config["NVIDIA_API_KEY"] = "nvapi-test"
        app.config["ANTHROPIC_API_KEY"] = None
        app.config["OPENAI_API_KEY"] = None
        app.config["GOOGLE_API_KEY"] = None
        # Bust any leftover cache from other tests.
        ai_service._CACHE.clear()
        result = ai_service.generate(
            "caption", "Topic: coffee\nPlatform: instagram\nTone: fun"
        )

    assert result["provider"] == "nvidia"
    assert result["cached"] is False
    assert result["result"].startswith("NVIDIA:")
