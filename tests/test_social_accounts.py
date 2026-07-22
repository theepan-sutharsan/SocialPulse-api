from tests.helpers import connect_demo, register


def test_connect_demo_backfills_history(auth, client):
    account = connect_demo(client, auth["headers"], "instagram", "@brand")
    assert account["is_demo"] is True
    hist = client.get(
        f"/api/social-accounts/{account['id']}/history?range=30d", headers=auth["headers"]
    ).get_json()
    assert len(hist["history"]) >= 30


def test_list_and_filter_accounts(auth, client):
    connect_demo(client, auth["headers"], "instagram", "@a")
    connect_demo(client, auth["headers"], "tiktok", "@b")
    resp = client.get("/api/social-accounts?platform=tiktok", headers=auth["headers"])
    assert resp.status_code == 200
    accts = resp.get_json()["social_accounts"]
    assert all(a["platform"] == "tiktok" for a in accts)


def test_duplicate_handle_rejected(auth, client):
    connect_demo(client, auth["headers"], "instagram", "@dup")
    resp = client.post(
        "/api/social-accounts/connect/instagram", json={"handle": "@dup"}, headers=auth["headers"]
    )
    assert resp.status_code == 409


def test_delete_account(auth, client):
    account = connect_demo(client, auth["headers"], "twitter", "@x")
    resp = client.delete(f"/api/social-accounts/{account['id']}", headers=auth["headers"])
    assert resp.status_code == 200


def test_isolation_between_workspaces(auth, client):
    account = connect_demo(client, auth["headers"], "instagram", "@mine")
    other = register(client)
    resp = client.get(f"/api/social-accounts/{account['id']}", headers=other["headers"])
    assert resp.status_code == 404
