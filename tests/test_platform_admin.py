from app.extensions import db
from app.models.user_model import User


def _make_admin(app, user_id):
    with app.app_context():
        user = db.session.get(User, user_id)
        user.is_platform_admin = True
        db.session.commit()


def test_non_admin_forbidden(auth, client):
    resp = client.get("/api/platform-admin/workspaces", headers=auth["headers"])
    assert resp.status_code == 403


def test_admin_lists_all_workspaces(app, auth, client):
    _make_admin(app, auth["user"]["id"])
    resp = client.get("/api/platform-admin/workspaces", headers=auth["headers"])
    assert resp.status_code == 200
    assert len(resp.get_json()["workspaces"]) >= 1


def test_admin_plan_override(app, auth, client):
    _make_admin(app, auth["user"]["id"])
    ws_id = auth["workspace"]["id"]
    resp = client.patch(
        f"/api/platform-admin/workspaces/{ws_id}/plan",
        json={"plan_tier": "agency"},
        headers=auth["headers"],
    )
    assert resp.status_code == 200
    assert resp.get_json()["workspace"]["plan_tier"] == "agency"
