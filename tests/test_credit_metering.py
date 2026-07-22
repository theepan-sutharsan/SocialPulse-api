def test_credits_deducted_per_generation(auth, client):
    client.post("/api/generate/caption", json={"topic": "unique-a"}, headers=auth["headers"])
    usage = client.get("/api/credit-usage/current", headers=auth["headers"]).get_json()
    assert usage["credit_usage"]["credits_used"] == 1


def test_free_tier_exhaustion_returns_402(auth, client):
    # Free tier = 5 credits; use distinct topics to avoid cache (no deduction on cache hit).
    for i in range(5):
        resp = client.post(
            "/api/generate/caption", json={"topic": f"topic-{i}"}, headers=auth["headers"]
        )
        assert resp.status_code == 201
    blocked = client.post(
        "/api/generate/caption", json={"topic": "topic-over"}, headers=auth["headers"]
    )
    assert blocked.status_code == 402


def test_cache_hit_is_not_charged(auth, client):
    payload = {"topic": "same-topic", "platform": "instagram", "tone": "fun"}
    client.post("/api/generate/caption", json=payload, headers=auth["headers"])
    client.post("/api/generate/caption", json=payload, headers=auth["headers"])
    usage = client.get("/api/credit-usage/current", headers=auth["headers"]).get_json()
    assert usage["credit_usage"]["credits_used"] == 1
