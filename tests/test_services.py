from datetime import date

from app.models.social_account_model import SocialAccount
from app.services import ai_service, mock_platform_service, snapshot_service


class _FakeAccount:
    id = 123
    platform = "instagram"
    handle = "@fake"


def test_mock_platform_is_deterministic():
    acct = _FakeAccount()
    a = mock_platform_service.point_for_date(acct, date(2026, 7, 1))
    b = mock_platform_service.point_for_date(acct, date(2026, 7, 1))
    assert a == b
    assert a["follower_count"] > 0


def test_mock_platform_grows_over_time():
    acct = _FakeAccount()
    early = mock_platform_service.point_for_date(acct, date(2026, 1, 1))
    later = mock_platform_service.point_for_date(acct, date(2026, 7, 1))
    assert later["follower_count"] >= early["follower_count"]


def test_ai_service_local_fallback(app):
    with app.app_context():
        result = ai_service.generate("caption", "Topic: coffee\nPlatform: instagram\nTone: fun")
        assert result["provider"] == "local-fallback"
        assert result["cached"] is False
        assert result["result"]


def test_snapshot_backfill_is_idempotent(app):
    with app.app_context():
        from app.extensions import db
        from app.models.workspace_model import Workspace

        ws = Workspace(name="S", slug="snap-ws", plan_tier="free")
        db.session.add(ws)
        db.session.flush()
        account = SocialAccount(workspace_id=ws.id, platform="tiktok", handle="@snap", is_demo=True)
        db.session.add(account)
        db.session.commit()

        first = snapshot_service.backfill_account(account, days=10)
        second = snapshot_service.backfill_account(account, days=10)
        assert first == 11  # 10 days + today
        assert second == 0  # unique constraint => no duplicates
