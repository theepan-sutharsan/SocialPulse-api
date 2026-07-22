"""Aggregated dashboard payload for the active workspace."""

from datetime import date, timedelta

from flask import jsonify
from flask_jwt_extended import current_user

from app.controllers.credit_usage_controller import get_or_create_current_usage
from app.middleware import current_workspace
from app.models.analytics_snapshot_model import AnalyticsSnapshot
from app.models.notification_model import Notification
from app.models.scheduled_post_model import ScheduledPost
from app.models.social_account_model import SocialAccount
from app.utils import utc_now


def _sparkline(account: SocialAccount, days: int = 14) -> list[int]:
    since = date.today() - timedelta(days=days)
    points = (
        AnalyticsSnapshot.query.filter(
            AnalyticsSnapshot.social_account_id == account.id,
            AnalyticsSnapshot.snapshot_date >= since,
        )
        .order_by(AnalyticsSnapshot.snapshot_date.asc())
        .all()
    )
    return [p.follower_count for p in points]


def get_dashboard():
    workspace = current_workspace
    accounts = SocialAccount.query.filter_by(workspace_id=workspace.id).all()

    account_summaries = []
    total_followers = 0
    for account in accounts:
        data = account.to_dict()
        total_followers += data["follower_count"]
        account_summaries.append({**data, "sparkline": _sparkline(account)})

    usage = get_or_create_current_usage(workspace)

    upcoming = (
        ScheduledPost.query.filter(
            ScheduledPost.workspace_id == workspace.id,
            ScheduledPost.status == "planned",
            ScheduledPost.scheduled_at >= utc_now(),
        )
        .order_by(ScheduledPost.scheduled_at.asc())
        .limit(5)
        .all()
    )

    notifications = (
        Notification.query.filter_by(user_id=current_user.id, workspace_id=workspace.id)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )

    return (
        jsonify(
            {
                "workspace": workspace.to_dict(),
                "summary": {
                    "connected_accounts": len(accounts),
                    "total_followers": total_followers,
                    "credits_used": usage.credits_used,
                    "credits_allotted": usage.credits_allotted,
                    "credits_remaining": usage.credits_remaining,
                    "upcoming_posts": len(upcoming),
                },
                "accounts": account_summaries,
                "credit_usage": usage.to_dict(),
                "upcoming_posts": [p.to_dict() for p in upcoming],
                "notifications": [n.to_dict() for n in notifications],
            }
        ),
        200,
    )
