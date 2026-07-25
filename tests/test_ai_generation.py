def test_generate_caption(auth, client):
    resp = client.post(
        "/api/generate/caption",
        json={"topic": "sunset photography", "platform": "instagram", "tone": "poetic"},
        headers=auth["headers"],
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["ai_generation"]["generation_type"] == "caption"
    assert body["ai_generation"]["result"]


def test_generate_requires_topic(auth, client):
    resp = client.post("/api/generate/caption", json={}, headers=auth["headers"])
    assert resp.status_code == 400


def test_generate_hashtags_and_list(auth, client):
    client.post(
        "/api/generate/hashtags", json={"topic": "fitness"}, headers=auth["headers"]
    )
    resp = client.get("/api/ai-generations?type=hashtags", headers=auth["headers"])
    assert resp.status_code == 200
    assert len(resp.get_json()["ai_generations"]) == 1


def test_delete_generation(auth, client):
    gen = client.post(
        "/api/generate/content-idea", json={"niche": "travel"}, headers=auth["headers"]
    ).get_json()["ai_generation"]
    resp = client.delete(f"/api/ai-generations/{gen['id']}", headers=auth["headers"])
    assert resp.status_code == 200


def test_lists_configured_ai_providers(auth, client, app):
    with app.app_context():
        app.config["OPENAI_API_KEY"] = "test-openai-key"
        app.config["AI_PRIMARY_PROVIDER"] = "openai"

    response = client.get("/api/generate/providers", headers=auth["headers"])

    assert response.status_code == 200
    assert response.get_json() == {
        "providers": ["openai"],
        "default_provider": "openai",
    }


def test_selected_provider_generates_with_that_provider(auth, client, app, monkeypatch):
    from app.services import ai_service

    with app.app_context():
        app.config["OPENAI_API_KEY"] = "test-openai-key"
        app.config["AI_PRIMARY_PROVIDER"] = "openai"
    monkeypatch.setitem(ai_service._PROVIDER_FUNCS, "openai", lambda prompt: "OpenAI result")

    response = client.post(
        "/api/generate/caption",
        json={"topic": "productivity", "provider": "openai"},
        headers=auth["headers"],
    )

    assert response.status_code == 201
    assert response.get_json()["ai_generation"]["provider"] == "openai"
    assert response.get_json()["ai_generation"]["result"] == "OpenAI result"


def test_rejects_unconfigured_selected_provider(auth, client):
    response = client.post(
        "/api/generate/caption",
        json={"topic": "productivity", "provider": "gemini"},
        headers=auth["headers"],
    )

    assert response.status_code == 400
    assert response.get_json()["errors"] == ["Selected AI provider is not configured."]