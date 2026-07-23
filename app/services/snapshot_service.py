"""Daily analytics snapshot job (SIGNATURE).

Builds exactly one ``AnalyticsSnapshot`` row per connected account per day. The
unique constraint on ``(social_account_id, snapshot_date)`` makes re-runs
idempotent. Live accounts pull from ``youtube_service``; demo accounts use the
deterministic ``mock_platform_service``.
"""

import logging
from datetime import date, timedelta

from app.extensions import db
from app.models.analytics_snapshot_model import AnalyticsSnapshot
from app.models.social_account_model import SocialAccount
from app.services import mock_platform_service, youtube_service
from app.utils.security import decrypt_token

logger = logging.getLogger(__name__)


def _upsert_snapshot(account: SocialAccount, snap_date: date, point: dict) -> bool:
    """Insert a snapshot if one doesn't exist for the day. Returns True if new."""
    exists = AnalyticsSnapshot.query.filter_by(
        social_account_id=account.id, snapshot_date=snap_date
    ).first()
    if exists:
        return False
    db.session.add(
        AnalyticsSnapshot(
            social_account_id=account.id,
            snapshot_date=snap_date,
            follower_count=point["follower_count"],
            view_count=point["view_count"],
            engagement_rate=point["engagement_rate"],
        )
    )
    return True


def _live_point(account: SocialAccount) -> dict | None:
    """Fetch a real data point for a YouTube account (OAuth or public), or None."""
    if account.platform != "youtube":
        return None

    # Public tracking via API key — real subscriber/view counts, no OAuth.
    if account.is_tracked and account.external_id:
        if not youtube_service.is_public_configured():
            return None
        try:
            stats = youtube_service.fetch_public_stats_by_channel_id(account.external_id)
            return {
                "follower_count": stats["subscriber_count"],
                "view_count": stats["view_count"],
                # Public stats expose no engagement; keep it honest (no fake value).
                "engagement_rate": 0.0,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Public YouTube fetch failed for account %s: %s", account.id, exc)
            return None

    if account.is_connected and account.access_token:
        try:
            token = decrypt_token(account.access_token)
            stats = youtube_service.fetch_channel_stats(token)
            engagement = mock_platform_service.generate_daily_point(account)["engagement_rate"]
            return {
                "follower_count": stats["subscriber_count"],
                "view_count": stats["view_count"],
                "engagement_rate": engagement,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Live YouTube fetch failed for account %s: %s", account.id, exc)
            return None
    return None


def backfill_account(account: SocialAccount, days: int = 30, seed_stats: dict | None = None) -> int:
    """Backfill ``days`` of history (plus today) so charts render immediately."""
    today = date.today()
    created = 0
    for offset in range(days, -1, -1):
        snap_date = today - timedelta(days=offset)
        point = mock_platform_service.point_for_date(account, snap_date)
        if seed_stats and offset == 0:
            point = {
                "follower_count": seed_stats.get("subscriber_count", point["follower_count"]),
                "view_count": seed_stats.get("view_count", point["view_count"]),
                "engagement_rate": point["engagement_rate"],
            }
        if _upsert_snapshot(account, snap_date, point):
            created += 1
    db.session.commit()
    return created


def record_public_snapshot(
    account: SocialAccount, stats: dict, snap_date: date | None = None
) -> bool:
    """Persist one real snapshot for a tracked (public) channel from ``stats``.

    Used right after a channel is tracked so the first data point is genuine and
    dated today — never a fabricated historical curve.
    """
    snap_date = snap_date or date.today()
    point = {
        "follower_count": int(stats.get("subscriber_count", 0) or 0),
        "view_count": int(stats.get("view_count", 0) or 0),
        "engagement_rate": 0.0,
    }
    created = _upsert_snapshot(account, snap_date, point)
    db.session.commit()
    return created


def snapshot_account(account: SocialAccount, snap_date: date | None = None) -> bool:
    snap_date = snap_date or date.today()
    point = _live_point(account)
    if point is None:
        # Tracked (public) channels only ever store real data — skip if the live
        # fetch is unavailable rather than fabricating a mock point.
        if account.is_tracked:
            return False
        point = mock_platform_service.point_for_date(account, snap_date)
    created = _upsert_snapshot(account, snap_date, point)
    db.session.commit()
    return created


def run_daily_snapshots() -> dict:
    """Snapshot every account once for today. Idempotent on re-run."""
    accounts = SocialAccount.query.all()
    created = 0
    for account in accounts:
        try:
            if snapshot_account(account):
                created += 1
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logger.error("Snapshot failed for account %s: %s", account.id, exc)
    logger.info("Daily snapshots complete: %s new rows across %s accounts.", created, len(accounts))
    return {"accounts": len(accounts), "created": created}
