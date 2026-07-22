from tests.helpers import connect_demo, set_plan


def test_export_blocked_on_free(auth, client):
    resp = client.get("/api/social-accounts/export?format=csv", headers=auth["headers"])
    assert resp.status_code == 403


def test_export_csv_on_pro(app, auth, client):
    connect_demo(client, auth["headers"], "instagram", "@export")
    set_plan(app, auth["workspace"]["id"], "pro")
    resp = client.get("/api/social-accounts/export?format=csv", headers=auth["headers"])
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert b"platform,handle,snapshot_date" in resp.data
