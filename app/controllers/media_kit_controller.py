"""Media kit: public read-only profile page data + owner/editor branding edit."""

from flask import jsonify, request

from app.extensions import db
from app.middleware import current_workspace
from app.models.social_account_model import SocialAccount
from app.models.workspace_model import Workspace


def _public_account(account: SocialAccount) -> dict:
    data = account.to_dict()
    return {
        "platform": data["platform"],
        "handle": data["handle"],
        "is_demo": data["is_demo"],
        "follower_count": data["follower_count"],
        "view_count": data["view_count"],
        "engagement_rate": data["engagement_rate"],
    }


def get_media_kit(workspace_slug: str):
    """Public — rendered media-kit payload for a workspace slug."""
    workspace = Workspace.query.filter_by(slug=workspace_slug).first()
    if workspace is None:
        return jsonify({"error": "Media kit not found."}), 404

    accounts = SocialAccount.query.filter_by(workspace_id=workspace.id).all()
    total_followers = sum(a.to_dict()["follower_count"] for a in accounts)
    rates = [a.to_dict()["engagement_rate"] for a in accounts if a.to_dict()["engagement_rate"]]
    avg_engagement = round(sum(rates) / len(rates), 2) if rates else 0.0

    return (
        jsonify(
            {
                "media_kit": {
                    "name": workspace.name,
                    "slug": workspace.slug,
                    "bio": workspace.bio,
                    "tagline": workspace.tagline,
                    "brand_color": workspace.brand_color,
                    "logo_url": workspace.logo_url,
                    "is_white_label": workspace.is_white_label,
                    "total_followers": total_followers,
                    "avg_engagement_rate": avg_engagement,
                    "featured_accounts": [_public_account(a) for a in accounts],
                }
            }
        ),
        200,
    )


def update_media_kit():
    """Owner/Editor — update branding, bio, tagline, logo (white-label = Agency)."""
    workspace = Workspace.query.get(current_workspace.id)
    data = request.get_json(silent=True) or {}

    if "bio" in data:
        workspace.bio = data["bio"]
    if "tagline" in data:
        workspace.tagline = data["tagline"]
    if "brand_color" in data:
        workspace.brand_color = data["brand_color"]
    if "logo_url" in data:
        workspace.logo_url = data["logo_url"]
    if "is_white_label" in data:
        if data["is_white_label"] and workspace.plan_tier != "agency":
            return jsonify({"error": "White-label branding requires the Agency plan."}), 403
        workspace.is_white_label = bool(data["is_white_label"])

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not update media kit."}), 500
    return jsonify({"message": "Media kit updated.", "workspace": workspace.to_dict()}), 200
