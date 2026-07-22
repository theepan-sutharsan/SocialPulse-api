def test_invite_member(auth, client):
    ws_id = auth["workspace"]["id"]
    resp = client.post(
        f"/api/workspaces/{ws_id}/members",
        json={"email": "editor@test.com", "role": "editor"},
        headers=auth["headers"],
    )
    assert resp.status_code == 201
    assert resp.get_json()["member"]["role"] == "editor"


def test_list_members_includes_owner(auth, client):
    ws_id = auth["workspace"]["id"]
    resp = client.get(f"/api/workspaces/{ws_id}/members", headers=auth["headers"])
    assert resp.status_code == 200
    roles = [m["role"] for m in resp.get_json()["members"]]
    assert "owner" in roles


def test_change_and_remove_member(auth, client):
    ws_id = auth["workspace"]["id"]
    member = client.post(
        f"/api/workspaces/{ws_id}/members",
        json={"email": "viewer@test.com", "role": "viewer"},
        headers=auth["headers"],
    ).get_json()["member"]
    up = client.put(
        f"/api/workspaces/{ws_id}/members/{member['id']}",
        json={"role": "editor"},
        headers=auth["headers"],
    )
    assert up.status_code == 200
    rm = client.delete(f"/api/workspaces/{ws_id}/members/{member['id']}", headers=auth["headers"])
    assert rm.status_code == 200


def test_cannot_remove_last_owner(auth, client):
    ws_id = auth["workspace"]["id"]
    owner = [
        m
        for m in client.get(f"/api/workspaces/{ws_id}/members", headers=auth["headers"]).get_json()["members"]
        if m["role"] == "owner"
    ][0]
    resp = client.delete(f"/api/workspaces/{ws_id}/members/{owner['id']}", headers=auth["headers"])
    assert resp.status_code == 400
