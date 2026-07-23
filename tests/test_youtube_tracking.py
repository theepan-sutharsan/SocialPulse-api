"""Tests for SocialBlade-style public YouTube tracking (API key, no OAuth).

Network calls to the YouTube Data API are monkeypatched so the suite runs
offline. The focus is on behaviour: source labelling, a single *real* snapshot
on track (no fabricated backfill), dedupe, and daily-snapshot handling.
"""

from datetime import date, timedelta

from app.extensions import db
from app.models.social_account_model import SocialAccount
from app.services import snapshot_service, youtube_service

_CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw"
CANNED = {
    "channel_id": _CHANNEL_ID,
    "handle": "Google Developers",
    "custom_url": "@googledevelopers",
    "subscriber_count": 2_000_000,
    "view_count": 300_000_000,
    "hidden_subscriber_count": False,
}


def _enable_public(monkeypatch, stats=CANNED):
    monkeypatch.setattr(youtube_service, "is_public_configured", lambda: True)
    monkeypatch.setattr(
        youtube_service, "fetch_public_channel_stats", lambda raw: dict(stats)
    )


def _track(client, auth, url="https://youtube.com/@googledevelopers"):
    return client.post(
        "/api/social-accounts/track/youtube",
        json={"url": url},
        headers=auth["headers"],
    )


def test_track_requires_configuration(auth, client, monkeypatch):
    monkeypatch.setattr(youtube_service, "is_public_configured", lambda: False)
    resp = _track(client, auth)
    assert resp.status_code == 503


def test_track_requires_url(auth, client, monkeypatch):
    _enable_public(monkeypatch)
    resp = client.post(
        "/api/social-accounts/track/youtube", json={}, headers=auth["headers"]
    )
    assert resp.status_code == 400


def test_track_creates_public_account_with_single_real_snapshot(auth, client, monkeypatch):
    _enable_public(monkeypatch)
    resp = _track(client, auth)
    assert resp.status_code == 201
    account = resp.get_json()["social_account"]

    assert account["source"] == "public"
    assert account["is_tracked"] is True
    assert account["is_demo"] is False
    assert account["is_connected"] is False
    assert account["handle"] == "Google Developers"
    assert account["follower_count"] == CANNED["subscriber_count"]

    # No fake historical backfill: exactly one real snapshot dated today.
    hist = client.get(
        f"/api/social-accounts/{account['id']}/history?range=90d",
        headers=auth["headers"],
    ).get_json()
    assert len(hist["history"]) == 1
    assert hist["history"][0]["snapshot_date"] == date.today().isoformat()
    assert hist["history"][0]["follower_count"] == CANNED["subscriber_count"]


def test_track_dedupes_same_channel_by_id(auth, client, monkeypatch):
    _enable_public(monkeypatch)
    assert _track(client, auth, "@googledevelopers").status_code == 201
    dup = _track(client, auth, f"https://youtube.com/channel/{_CHANNEL_ID}")
    assert dup.status_code == 409


def test_track_channel_not_found_returns_404(auth, client, monkeypatch):
    monkeypatch.setattr(youtube_service, "is_public_configured", lambda: True)

    def _raise(_raw):
        raise LookupError("No YouTube channel found for that URL or handle.")

    monkeypatch.setattr(youtube_service, "fetch_public_channel_stats", _raise)
    resp = _track(client, auth, "@definitely-not-a-real-channel-xyz")
    assert resp.status_code == 404


def test_daily_snapshot_appends_real_point_for_tracked(app, auth, client, monkeypatch):
    _enable_public(monkeypatch)
    account_id = _track(client, auth).get_json()["social_account"]["id"]

    grown = {**CANNED, "subscriber_count": 2_000_500, "view_count": 300_100_000}
    monkeypatch.setattr(
        youtube_service, "fetch_public_stats_by_channel_id", lambda cid: dict(grown)
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
    assert hist["history"][-1]["follower_count"] == 2_000_500


def test_daily_snapshot_skips_tracked_when_unavailable(app, auth, client, monkeypatch):
    _enable_public(monkeypatch)
    account_id = _track(client, auth).get_json()["social_account"]["id"]

    # Public fetch now unavailable — must NOT fabricate a mock data point.
    monkeypatch.setattr(youtube_service, "is_public_configured", lambda: False)

    with app.app_context():
        account = db.session.get(SocialAccount, account_id)
        created = snapshot_service.snapshot_account(
            account, snap_date=date.today() + timedelta(days=2)
        )
        assert created is False

    hist = client.get(
        f"/api/social-accounts/{account_id}/history?range=90d",
        headers=auth["headers"],
    ).get_json()
    assert len(hist["history"]) == 1
