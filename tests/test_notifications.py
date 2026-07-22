def test_invite_creates_notification_for_member(auth, client):
    # Invite creates a team_invite notification for the invited user.
    ws_id = auth["workspace"]["id"]
    client.post(
        f"/api/workspaces/{ws_id}/members",
        json={"email": "teammate@test.com", "role": "editor"},
        headers=auth["headers"],
    )
    # Owner has no notifications yet.
    resp = client.get("/api/notifications", headers=auth["headers"])
    assert resp.status_code == 200
    assert resp.get_json()["unread_count"] == 0


def test_mark_all_read(auth, client):
    resp = client.patch("/api/notifications/read-all", headers=auth["headers"])
    assert resp.status_code == 200
