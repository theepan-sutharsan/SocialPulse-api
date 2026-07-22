"""AI-credit ledger helpers + the current-usage endpoint.

Credit periods are monthly, keyed by the first day of the month. These helpers
are the single source of truth for credit checks/deductions used by the AI
generation flow and by billing when a plan changes.
"""

from datetime import date

from flask import jsonify

from app.config import Config
from app.extensions import db
from app.middleware import current_workspace
from app.models.credit_usage_model import CreditUsage


def current_period_start(today: date | None = None) -> date:
    today = today or date.today()
    return today.replace(day=1)


def get_or_create_current_usage(workspace) -> CreditUsage:
    """Return this month's ledger row for a workspace, creating it if needed."""
    period = current_period_start()
    usage = CreditUsage.query.filter_by(
        workspace_id=workspace.id, period_start=period
    ).first()
    if usage is None:
        allotted = Config.PLAN_CREDITS.get(workspace.plan_tier, 5)
        usage = CreditUsage(
            workspace_id=workspace.id,
            period_start=period,
            credits_allotted=allotted,
            credits_used=0,
        )
        db.session.add(usage)
        db.session.commit()
    return usage


def has_available_credits(workspace, amount: int = 1) -> bool:
    usage = get_or_create_current_usage(workspace)
    return usage.credits_used + amount <= usage.credits_allotted


def consume_credits(workspace, amount: int = 1) -> CreditUsage:
    """Deduct credits (called only on a successful, non-cached generation)."""
    usage = get_or_create_current_usage(workspace)
    usage.credits_used += amount
    db.session.commit()
    return usage


def get_current_usage():
    """GET /api/credit-usage/current — credits allotted vs used this period."""
    usage = get_or_create_current_usage(current_workspace)
    return jsonify({"credit_usage": usage.to_dict()}), 200
