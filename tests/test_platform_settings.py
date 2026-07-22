"""Tests for platform feature-flag settings (public read + admin management)."""

from app.extensions import db
from app.models.user_model import User


def _make_admin(app, user_id):
    with app.app_context():
        user = db.session.get(User, user_id)
        user.is_platform_admin = True
        db.session.commit()


def test_public_flags_available_without_auth(client):
    resp = client.get("/api/settings/public")
    assert resp.status_code == 200
    flags = resp.get_json()["feature_flags"]
    # Ships enabled by default so the shortcut works out of the box.
    assert flags["keyboard_theme_toggle"] is True


def test_non_admin_cannot_read_admin_settings(auth, client):
    resp = client.get("/api/platform-admin/settings", headers=auth["headers"])
    assert resp.status_code == 403


def test_non_admin_cannot_update_settings(auth, client):
    resp = client.put(
        "/api/platform-admin/settings",
        json={"feature_flags": {"keyboard_theme_toggle": False}},
        headers=auth["headers"],
    )
    assert resp.status_code == 403


def test_admin_toggles_flag_and_public_reflects_it(app, auth, client):
    _make_admin(app, auth["user"]["id"])

    resp = client.put(
        "/api/platform-admin/settings",
        json={"feature_flags": {"keyboard_theme_toggle": False}},
        headers=auth["headers"],
    )
    assert resp.status_code == 200
    assert resp.get_json()["feature_flags"]["keyboard_theme_toggle"] is False

    # The public endpoint now serves the admin's choice to every visitor.
    public = client.get("/api/settings/public").get_json()["feature_flags"]
    assert public["keyboard_theme_toggle"] is False


def test_admin_rejects_unknown_flag(app, auth, client):
    _make_admin(app, auth["user"]["id"])
    resp = client.put(
        "/api/platform-admin/settings",
        json={"feature_flags": {"nope_not_real": True}},
        headers=auth["headers"],
    )
    assert resp.status_code == 400
