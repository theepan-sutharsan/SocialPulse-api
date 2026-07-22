from tests.helpers import connect_demo


def test_dashboard_summary(auth, client):
    connect_demo(client, auth["headers"], "instagram", "@dash")
    resp = client.get("/api/me/dashboard", headers=auth["headers"])
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["summary"]["connected_accounts"] == 1
    assert "credit_usage" in body
    assert isinstance(body["accounts"][0]["sparkline"], list)
