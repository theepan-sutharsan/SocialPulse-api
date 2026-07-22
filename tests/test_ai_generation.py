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
