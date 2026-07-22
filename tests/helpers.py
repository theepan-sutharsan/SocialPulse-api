"""Shared test helpers."""

import uuid


def register(client, password="Password123", full_name="Test User", workspace_name="Test WS"):
    email = f"user-{uuid.uuid4().hex[:8]}@test.com"
    resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "workspace_name": workspace_name,
        },
    )
    data = resp.get_json()
    workspace = data["workspaces"][0]
    return {
        "email": email,
        "password": password,
        "token": data["access_token"],
        "user": data["user"],
        "workspace": workspace,
        "headers": {
            "Authorization": f"Bearer {data['access_token']}",
            "X-Workspace-Id": str(workspace["id"]),
        },
    }


def connect_demo(client, headers, platform="instagram", handle="@demo"):
    resp = client.post(
        f"/api/social-accounts/connect/{platform}",
        json={"handle": handle},
        headers=headers,
    )
    return resp.get_json()["social_account"]


def set_plan(app, workspace_id, plan_tier):
    """Directly set a workspace plan (bypasses billing) for test setup."""
    from app.extensions import db
    from app.models.workspace_model import Workspace

    with app.app_context():
        ws = Workspace.query.get(workspace_id)
        ws.plan_tier = plan_tier
        db.session.commit()
