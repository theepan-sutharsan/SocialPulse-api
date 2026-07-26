"""Unit tests for Instagram Webhook verification and event handling."""

def test_instagram_webhook_verification_success(client, app):
    app.config["INSTAGRAM_VERIFY_TOKEN"] = "test_token_123"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "test_token_123",
        "hub.challenge": "1158201444",
    }
    resp = client.get("/api/webhook/instagram", query_string=params)
    assert resp.status_code == 200
    assert resp.data.decode("utf-8") == "1158201444"


def test_instagram_webhook_verification_invalid_token(client, app):
    app.config["INSTAGRAM_VERIFY_TOKEN"] = "test_token_123"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "1158201444",
    }
    resp = client.get("/api/webhook/instagram", query_string=params)
    assert resp.status_code == 403


def test_instagram_webhook_verification_missing_config(client, app):
    app.config["INSTAGRAM_VERIFY_TOKEN"] = ""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "any_token",
        "hub.challenge": "1158201444",
    }
    resp = client.get("/api/webhook/instagram", query_string=params)
    assert resp.status_code == 403


def test_instagram_webhook_post_event(client):
    payload = {"object": "instagram", "entry": [{"id": "17841400000000000", "time": 1600000000}]}
    resp = client.post("/api/webhook/instagram", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
