"""Scheduled posts blueprint — /api/scheduled-posts."""

from flask import Blueprint

from app.controllers import scheduled_post_controller as ctrl
from app.middleware import ALL_ROLES, EDITOR_ROLES, roles_required

scheduled_post_bp = Blueprint(
    "scheduled_posts", __name__, url_prefix="/api/scheduled-posts"
)


@scheduled_post_bp.post("")
@roles_required(*EDITOR_ROLES)
def create_post():
    return ctrl.create_scheduled_post()


@scheduled_post_bp.get("")
@roles_required(*ALL_ROLES)
def list_posts():
    return ctrl.get_scheduled_posts()


@scheduled_post_bp.get("/<int:post_id>")
@roles_required(*ALL_ROLES)
def get_post(post_id):
    return ctrl.get_scheduled_post(post_id)


@scheduled_post_bp.put("/<int:post_id>")
@roles_required(*EDITOR_ROLES)
def update_post(post_id):
    return ctrl.update_scheduled_post(post_id)


@scheduled_post_bp.patch("/<int:post_id>/cancel")
@roles_required(*EDITOR_ROLES)
def cancel_post(post_id):
    return ctrl.cancel_scheduled_post(post_id)
