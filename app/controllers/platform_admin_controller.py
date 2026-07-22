"""Platform-admin endpoints (cross-workspace). Protected by ``platform_admin``."""

from flask import jsonify, request

from app.controllers.credit_usage_controller import get_or_create_current_usage
from app.config import Config
from app.extensions import db
from app.models.social_account_model import SocialAccount
from app.models.subscription_model import PLAN_TIERS, Subscription
from app.models.workspace_member_model import WorkspaceMember
from app.models.workspace_model import Workspace


def list_workspaces():
    workspaces = Workspace.query.order_by(Workspace.created_at.desc()).all()
    payload = []
    for workspace in workspaces:
        owner = (
            WorkspaceMember.query.filter_by(workspace_id=workspace.id, role="owner")
            .first()
        )
        payload.append(
            {
                **workspace.to_dict(),
                "owner_email": owner.user.email if owner and owner.user else None,
                "account_count": SocialAccount.query.filter_by(
                    workspace_id=workspace.id
                ).count(),
            }
        )
    return jsonify({"workspaces": payload}), 200


def get_workspace(workspace_id: int):
    workspace = Workspace.query.get(workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found."}), 404
    members = WorkspaceMember.query.filter_by(workspace_id=workspace_id).all()
    accounts = SocialAccount.query.filter_by(workspace_id=workspace_id).all()
    return (
        jsonify(
            {
                "workspace": workspace.to_dict(),
                "members": [m.to_dict() for m in members],
                "social_accounts": [a.to_dict() for a in accounts],
            }
        ),
        200,
    )


def update_plan(workspace_id: int):
    workspace = Workspace.query.get(workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found."}), 404
    data = request.get_json(silent=True) or {}
    plan_tier = data.get("plan_tier")
    if plan_tier not in PLAN_TIERS:
        return jsonify({"errors": [f"plan_tier must be one of: {', '.join(PLAN_TIERS)}."]}), 400

    workspace.plan_tier = plan_tier
    workspace.is_agency = plan_tier == "agency"
    subscription = Subscription.query.filter_by(workspace_id=workspace_id).first()
    if subscription:
        subscription.plan_tier = plan_tier

    # Reset the current period's credit allotment to the new plan.
    usage = get_or_create_current_usage(workspace)
    usage.credits_allotted = Config.PLAN_CREDITS.get(plan_tier, usage.credits_allotted)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not update plan."}), 500
    return jsonify({"message": "Plan updated.", "workspace": workspace.to_dict()}), 200
