from tests.helpers import register


def test_missing_token_rejected(client):
    assert client.get("/api/me/dashboard").status_code == 401


def test_viewer_cannot_generate_but_can_view(auth, client):
    # Invite an existing user as viewer, then act as that viewer in the workspace.
    viewer = register(client)
    ws_id = auth["workspace"]["id"]
    client.post(
        f"/api/workspaces/{ws_id}/members",
        json={"email": viewer["email"], "role": "viewer"},
        headers=auth["headers"],
    )
    viewer_headers = {
        "Authorization": f"Bearer {viewer['token']}",
        "X-Workspace-Id": str(ws_id),
    }
    # Viewer can read the dashboard...
    assert client.get("/api/me/dashboard", headers=viewer_headers).status_code == 200
    # ...but cannot generate AI content.
    blocked = client.post(
        "/api/generate/caption", json={"topic": "x"}, headers=viewer_headers
    )
    assert blocked.status_code == 403


def test_non_member_cannot_use_workspace(auth, client):
    outsider = register(client)
    headers = {
        "Authorization": f"Bearer {outsider['token']}",
        "X-Workspace-Id": str(auth["workspace"]["id"]),
    }
    assert client.get("/api/me/dashboard", headers=headers).status_code == 403
