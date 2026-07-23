"""Tests for real Instagram connect (Meta Graph API OAuth) + demo fallback.

All Meta network calls are monkeypatched so the suite runs offline. The focus
is on behaviour: OAuth kickoff, code completion with a single *real* snapshot
(no fabricated backfill), the demo fallback, dedupe, and daily-snapshot handling
for a connected account.
"""

from datetime import date, timedelta

from app.extensions import db
from app.models.social_account_model import SocialAccount
from app.services import instagram_service, snapshot_service

_CONNECT = "/api/social-accounts/connect/instagram"

STATS = {
    "external_id": "178414",
    "username": "brand.official",
    "account_type": "BUSINESS",
    "follower_count": 54_000,
    "media_count": 320,
}


def _enable_oauth(monkeypatch):
    monkeypatch.setattr(instagram_service, "is_configured", lambda: True)
    monkeypatch.setattr(
        instagram_service,
        "get_authorization_url",
        lambda: ("https://auth.test/ig", "state-123"),
    )


def _enable_code_exchange(monkeypatch, stats=STATS):
    monkeypatch.setattr(
        instagram_service,
        "exchange_code",
        lambda code: {
            "access_token": "long-lived-token",
            "user_id": stats["external_id"],
        },
    )
    monkeypatch.setattr(
        instagram_service, "fetch_profile_stats", lambda token, uid=None: dict(stats)
    )


def test_connect_returns_authorization_url_when_configured(auth, client, monkeypatch):
    _enable_oauth(monkeypatch)
    resp = client.post(_CONNECT, json={}, headers=auth["headers"])
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["authorization_url"] == "https://auth.test/ig"
    assert body["state"] == "state-123"


def test_connect_falls_back_to_demo_when_not_configured(auth, client, monkeypatch):
    monkeypatch.setattr(instagram_service, "is_configured", lambda: False)
    resp = client.post(_CONNECT, json={"handle": "@brand"}, headers=auth["headers"])
    assert resp.status_code == 201
    account = resp.get_json()["social_account"]
    assert account["source"] == "demo"
    assert account["is_demo"] is True
    assert account["platform"] == "instagram"

    # Demo accounts get a mock backfill so charts render immediately.
    hist = client.get(
        f"/api/social-accounts/{account['id']}/history?range=90d",
        headers=auth["headers"],
    ).get_json()
    assert len(hist["history"]) >= 30


def test_demo_flag_forces_demo_even_when_configured(auth, client, monkeypatch):
    _enable_oauth(monkeypatch)
    resp = client.post(
        _CONNECT, json={"handle": "@brand", "demo": True}, headers=auth["headers"]
    )
    assert resp.status_code == 201
    assert resp.get_json()["social_account"]["source"] == "demo"


def test_connect_requires_handle_for_demo(auth, client, monkeypatch):
    monkeypatch.setattr(instagram_service, "is_configured", lambda: False)
    resp = client.post(_CONNECT, json={}, headers=auth["headers"])
    assert resp.status_code == 400


def test_connect_completes_with_code_single_real_snapshot(auth, client, monkeypatch):
    _enable_code_exchange(monkeypatch)
    resp = client.post(_CONNECT, json={"code": "oauth-code"}, headers=auth["headers"])
    assert resp.status_code == 201
    account = resp.get_json()["social_account"]

    assert account["source"] == "oauth"
    assert account["is_connected"] is True
    assert account["is_demo"] is False
    assert account["is_tracked"] is False
    assert account["handle"] == STATS["username"]
    assert account["follower_count"] == STATS["follower_count"]

    # No fabricated history: exactly one real snapshot dated today.
    hist = client.get(
        f"/api/social-accounts/{account['id']}/history?range=90d",
        headers=auth["headers"],
    ).get_json()
    assert len(hist["history"]) == 1
    assert hist["history"][0]["snapshot_date"] == date.today().isoformat()


def test_connect_dedupes_same_handle(auth, client, monkeypatch):
    _enable_code_exchange(monkeypatch)
    first = client.post(_CONNECT, json={"code": "c1"}, headers=auth["headers"])
    assert first.status_code == 201
    dup = client.post(_CONNECT, json={"code": "c2"}, headers=auth["headers"])
    assert dup.status_code == 409


def test_connect_surfaces_upstream_failure(auth, client, monkeypatch):
    def _raise(code):
        raise RuntimeError("token exchange failed")

    monkeypatch.setattr(instagram_service, "exchange_code", _raise)
    resp = client.post(_CONNECT, json={"code": "bad"}, headers=auth["headers"])
    assert resp.status_code == 502


def test_daily_snapshot_appends_real_point_for_connected(app, auth, client, monkeypatch):
    _enable_code_exchange(monkeypatch)
    account_id = client.post(
        _CONNECT, json={"code": "c1"}, headers=auth["headers"]
    ).get_json()["social_account"]["id"]

    grown = {**STATS, "follower_count": 54_250}
    monkeypatch.setattr(
        instagram_service, "fetch_profile_stats", lambda token, uid=None: dict(grown)
    )
    with app.app_context():
        account = db.session.get(SocialAccount, account_id)
        created = snapshot_service.snapshot_account(
            account, snap_date=date.today() + timedelta(days=1)
        )
        assert created is True

    hist = client.get(
        f"/api/social-accounts/{account_id}/history?range=90d",
        headers=auth["headers"],
    ).get_json()
    assert len(hist["history"]) == 2
    assert hist["history"][-1]["follower_count"] == 54_250


def test_daily_snapshot_skips_connected_when_unavailable(app, auth, client, monkeypatch):
    _enable_code_exchange(monkeypatch)
    account_id = client.post(
        _CONNECT, json={"code": "c1"}, headers=auth["headers"]
    ).get_json()["social_account"]["id"]

    def _raise(token, uid=None):
        raise RuntimeError("Instagram API down")

    monkeypatch.setattr(instagram_service, "fetch_profile_stats", _raise)
    with app.app_context():
        account = db.session.get(SocialAccount, account_id)
        created = snapshot_service.snapshot_account(
            account, snap_date=date.today() + timedelta(days=2)
        )
        # Never fabricate mock data for a real (connected) account.
        assert created is False

    hist = client.get(
        f"/api/social-accounts/{account_id}/history?range=90d",
        headers=auth["headers"],
    ).get_json()
    assert len(hist["history"]) == 1
