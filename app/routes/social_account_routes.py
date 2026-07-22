"""Social accounts blueprint — /api/social-accounts."""

from flask import Blueprint

from app.controllers import social_account_controller as ctrl
from app.middleware import ALL_ROLES, EDITOR_ROLES, OWNER_ONLY, roles_required

social_account_bp = Blueprint(
    "social_accounts", __name__, url_prefix="/api/social-accounts"
)


@social_account_bp.get("")
@roles_required(*ALL_ROLES)
def list_accounts():
    return ctrl.get_social_accounts()


@social_account_bp.post("/connect/youtube")
@roles_required(*EDITOR_ROLES)
def connect_youtube():
    return ctrl.connect_youtube()


@social_account_bp.get("/connect/youtube/callback")
def youtube_callback():
    return ctrl.youtube_callback()


@social_account_bp.post("/connect/<platform>")
@roles_required(*EDITOR_ROLES)
def connect_demo(platform):
    return ctrl.connect_demo_platform(platform)


@social_account_bp.get("/export")
@roles_required(*OWNER_ONLY)
def export_accounts():
    return ctrl.export_accounts()


@social_account_bp.get("/<int:account_id>")
@roles_required(*ALL_ROLES)
def get_account(account_id):
    return ctrl.get_social_account(account_id)


@social_account_bp.get("/<int:account_id>/history")
@roles_required(*ALL_ROLES)
def get_history(account_id):
    return ctrl.get_history(account_id)


@social_account_bp.get("/<int:account_id>/grade")
@roles_required(*ALL_ROLES)
def get_grade(account_id):
    return ctrl.get_grade(account_id)


@social_account_bp.delete("/<int:account_id>")
@roles_required(*EDITOR_ROLES)
def delete_account(account_id):
    return ctrl.delete_social_account(account_id)
