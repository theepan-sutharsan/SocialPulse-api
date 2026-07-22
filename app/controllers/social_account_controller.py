"""Social accounts: connect (live YouTube OAuth / demo platforms), list, detail,
history time-series, composite grade + milestone projection, delete, and export.

Every query is scoped to ``current_workspace.id`` for tenant isolation.
"""

from datetime import date, timedelta

from flask import jsonify, redirect, request

from app.config import Config
from app.extensions import db
from app.middleware import current_workspace
from app.models.analytics_snapshot_model import AnalyticsSnapshot
from app.models.social_account_model import PLATFORMS, SocialAccount
from app.services import mock_platform_service, snapshot_service, youtube_service
from app.utils import utc_now
from app.utils.csv_utils import rows_to_csv_response
from app.utils.pdf_utils import document_pdf_response
from app.utils.security import encrypt_token

DEMO_PLATFORMS = ("instagram", "tiktok", "twitter")
RANGE_DAYS = {"7d": 7, "30d": 30, "90d": 90}


def _get_account_or_none(account_id: int) -> SocialAccount | None:
    return SocialAccount.query.filter_by(
        id=account_id, workspace_id=current_workspace.id
    ).first()


def get_social_accounts():
    query = SocialAccount.query.filter_by(workspace_id=current_workspace.id)
    platform = request.args.get("platform")
    if platform:
        query = query.filter_by(platform=platform)
    accounts = query.order_by(SocialAccount.created_at.desc()).all()
    return jsonify({"social_accounts": [a.to_dict() for a in accounts]}), 200


def connect_youtube():
    """Start live OAuth (returns an authorization URL) or, when OAuth isn't
    configured locally, create a live-shaped seeded account so the demo works.
    """
    data = request.get_json(silent=True) or {}
    code = data.get("code") or request.args.get("code")

    if code:
        return _complete_youtube_connection(code, data)

    if youtube_service.is_configured():
        auth_url, state = youtube_service.get_authorization_url()
        return jsonify({"authorization_url": auth_url, "state": state}), 200

    # Local dev fallback — seeded live-shaped account (spec §19).
    handle = (data.get("handle") or "My YouTube Channel").strip()
    return _create_youtube_account(handle=handle, access_token=None, is_demo=False)


def youtube_callback():
    """OAuth redirect target. Bounces the code back to the SPA, which re-posts
    it to ``/connect/youtube`` with the authenticated workspace context."""
    code = request.args.get("code")
    state = request.args.get("state", "")
    if not code:
        return jsonify({"error": "Missing OAuth code."}), 400
    return redirect(
        f"{Config.FRONTEND_URL}/accounts/connect?provider=youtube&code={code}&state={state}"
    )


def _complete_youtube_connection(code: str, data: dict):
    try:
        tokens = youtube_service.exchange_code(code)
        stats = youtube_service.fetch_channel_stats(tokens["access_token"])
    except Exception as exc:  # noqa: BLE001 - surface as a clean API error
        return jsonify({"error": f"YouTube connection failed: {exc}"}), 502
    return _create_youtube_account(
        handle=stats.get("handle") or data.get("handle") or "YouTube Channel",
        access_token=tokens.get("access_token"),
        refresh_token=tokens.get("refresh_token"),
        is_demo=False,
        seed_stats=stats,
    )


def _create_youtube_account(
    handle, access_token=None, refresh_token=None, is_demo=False, seed_stats=None
):
    existing = SocialAccount.query.filter_by(
        workspace_id=current_workspace.id, platform="youtube", handle=handle
    ).first()
    if existing:
        return jsonify({"error": "This YouTube account is already connected."}), 409
    try:
        account = SocialAccount(
            workspace_id=current_workspace.id,
            platform="youtube",
            handle=handle,
            is_demo=is_demo,
            access_token=encrypt_token(access_token),
            refresh_token=encrypt_token(refresh_token),
            connected_at=utc_now() if access_token else utc_now(),
        )
        db.session.add(account)
        db.session.commit()
        snapshot_service.backfill_account(account, days=30, seed_stats=seed_stats)
        return (
            jsonify(
                {"message": "YouTube account connected.", "social_account": account.to_dict()}
            ),
            201,
        )
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not connect YouTube account."}), 500


def connect_demo_platform(platform: str):
    platform = (platform or "").lower()
    if platform not in DEMO_PLATFORMS:
        return (
            jsonify(
                {"error": f"Demo connect supports: {', '.join(DEMO_PLATFORMS)}."}
            ),
            400,
        )
    data = request.get_json(silent=True) or {}
    handle = (data.get("handle") or "").strip()
    if not handle:
        return jsonify({"errors": ["A handle is required."]}), 400

    if SocialAccount.query.filter_by(
        workspace_id=current_workspace.id, platform=platform, handle=handle
    ).first():
        return jsonify({"error": "This account is already connected."}), 409
    try:
        account = SocialAccount(
            workspace_id=current_workspace.id,
            platform=platform,
            handle=handle,
            is_demo=True,
        )
        db.session.add(account)
        db.session.commit()
        snapshot_service.backfill_account(account, days=30)
        return (
            jsonify(
                {
                    "message": f"{platform.title()} connected in Demo Mode.",
                    "social_account": account.to_dict(),
                }
            ),
            201,
        )
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not connect account."}), 500


def get_social_account(account_id: int):
    account = _get_account_or_none(account_id)
    if account is None:
        return jsonify({"error": "Social account not found."}), 404
    return jsonify({"social_account": account.to_dict()}), 200


def get_history(account_id: int):
    account = _get_account_or_none(account_id)
    if account is None:
        return jsonify({"error": "Social account not found."}), 404

    query = AnalyticsSnapshot.query.filter_by(social_account_id=account.id)
    range_key = request.args.get("range", "30d")
    if range_key in RANGE_DAYS:
        since = date.today() - timedelta(days=RANGE_DAYS[range_key])
        query = query.filter(AnalyticsSnapshot.snapshot_date >= since)
    snapshots = query.order_by(AnalyticsSnapshot.snapshot_date.asc()).all()
    return (
        jsonify(
            {
                "social_account": account.to_dict(),
                "range": range_key,
                "is_demo": account.is_demo,
                "history": [s.to_dict() for s in snapshots],
            }
        ),
        200,
    )


def get_grade(account_id: int):
    account = _get_account_or_none(account_id)
    if account is None:
        return jsonify({"error": "Social account not found."}), 404
    snapshots = (
        AnalyticsSnapshot.query.filter_by(social_account_id=account.id)
        .order_by(AnalyticsSnapshot.snapshot_date.asc())
        .all()
    )
    return jsonify({"social_account_id": account.id, **_grade_report(snapshots)}), 200


def delete_social_account(account_id: int):
    account = _get_account_or_none(account_id)
    if account is None:
        return jsonify({"error": "Social account not found."}), 404
    try:
        db.session.delete(account)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not delete account."}), 500
    return jsonify({"message": "Social account disconnected."}), 200


def export_accounts():
    """CSV/PDF export of analytics history — Pro/Agency tiers only."""
    if current_workspace.plan_tier not in ("pro", "agency"):
        return (
            jsonify({"error": "Export is available on Pro and Agency plans. Upgrade to continue."}),
            403,
        )
    accounts = SocialAccount.query.filter_by(workspace_id=current_workspace.id).all()
    fmt = request.args.get("format", "csv").lower()

    if fmt == "pdf":
        return _export_pdf(accounts)
    return _export_csv(accounts)


def _export_csv(accounts):
    headers = [
        "platform",
        "handle",
        "snapshot_date",
        "follower_count",
        "view_count",
        "engagement_rate",
    ]
    rows = []
    for account in accounts:
        for snap in account.snapshots:
            rows.append(
                [
                    account.platform,
                    account.handle,
                    snap.snapshot_date.isoformat(),
                    snap.follower_count,
                    snap.view_count,
                    float(snap.engagement_rate or 0),
                ]
            )
    filename = f"{current_workspace.slug}-analytics.csv"
    return rows_to_csv_response(filename, headers, rows)


def _export_pdf(accounts):
    sections = []
    for account in accounts:
        recent = account.snapshots[-30:]
        table_rows = [
            [
                s.snapshot_date.isoformat(),
                s.follower_count,
                s.view_count,
                float(s.engagement_rate or 0),
            ]
            for s in recent
        ]
        sections.append(
            {
                "heading": f"{account.platform.title()} — {account.handle}"
                + (" (Demo Mode)" if account.is_demo else ""),
                "table": {
                    "headers": ["Date", "Followers", "Views", "Engagement %"],
                    "rows": table_rows,
                },
            }
        )
    period = f"Generated {date.today().isoformat()}"
    filename = f"{current_workspace.slug}-growth-report.pdf"
    return document_pdf_response(
        filename, f"{current_workspace.name} — Growth Report", sections, subtitle=period
    )


# --- Grade + milestone projection -------------------------------------------------


def _grade_report(snapshots) -> dict:
    if len(snapshots) < 2:
        return {
            "grade": "N/A",
            "score": 0,
            "daily_gain": 0,
            "growth_percent": 0,
            "engagement_rate": (
                float(snapshots[-1].engagement_rate) if snapshots else 0.0
            ),
            "milestone": None,
        }

    first, last = snapshots[0], snapshots[-1]
    days = max((last.snapshot_date - first.snapshot_date).days, 1)
    total_gain = last.follower_count - first.follower_count
    daily_gain = total_gain / days
    growth_percent = (
        (total_gain / first.follower_count * 100) if first.follower_count else 0.0
    )
    engagement = float(last.engagement_rate or 0)

    score = _score(growth_percent, engagement)
    return {
        "grade": _grade_letter(score),
        "score": round(score, 1),
        "daily_gain": round(daily_gain, 1),
        "growth_percent": round(growth_percent, 2),
        "engagement_rate": engagement,
        "current_followers": last.follower_count,
        "milestone": _project_milestone(last.follower_count, daily_gain),
    }


def _score(growth_percent: float, engagement: float) -> float:
    growth_score = min(max(growth_percent, 0) * 4, 60)  # up to 60 points
    engagement_score = min(engagement * 8, 40)  # up to 40 points
    return growth_score + engagement_score


def _grade_letter(score: float) -> str:
    thresholds = [
        (95, "A++"),
        (88, "A+"),
        (78, "A"),
        (68, "B+"),
        (58, "B"),
        (45, "C"),
        (30, "D"),
    ]
    for cutoff, letter in thresholds:
        if score >= cutoff:
            return letter
    return "F"


def _project_milestone(current: int, daily_gain: float) -> dict | None:
    if current < 1000:
        step = 1000
    elif current < 10000:
        step = 5000
    elif current < 100000:
        step = 50000
    elif current < 1_000_000:
        step = 250000
    else:
        step = 1_000_000
    target = ((current // step) + 1) * step
    if daily_gain <= 0:
        return {"target": target, "days_to_reach": None, "eta": None}
    days = int((target - current) / daily_gain)
    eta = (date.today() + timedelta(days=days)).isoformat()
    return {"target": target, "days_to_reach": days, "eta": eta}
