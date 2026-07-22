def test_plans_public(client):
    resp = client.get("/api/billing/plans")
    assert resp.status_code == 200
    tiers = [p["tier"] for p in resp.get_json()["plans"]]
    assert tiers == ["free", "pro", "agency"]


def test_simulated_checkout_upgrades_plan(auth, client):
    resp = client.post(
        "/api/billing/checkout",
        json={"plan_tier": "pro", "provider": "stripe"},
        headers=auth["headers"],
    )
    assert resp.status_code == 200
    assert "checkout_url" in resp.get_json()
    sub = client.get("/api/billing/subscription", headers=auth["headers"]).get_json()
    assert sub["subscription"]["plan_tier"] == "pro"


def test_checkout_rejects_free_tier(auth, client):
    resp = client.post(
        "/api/billing/checkout", json={"plan_tier": "free", "provider": "stripe"}, headers=auth["headers"]
    )
    assert resp.status_code == 400


def test_cancel_reverts_to_free(auth, client):
    client.post(
        "/api/billing/checkout", json={"plan_tier": "pro", "provider": "stripe"}, headers=auth["headers"]
    )
    resp = client.post("/api/billing/cancel", headers=auth["headers"])
    assert resp.status_code == 200
