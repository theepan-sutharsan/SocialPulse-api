"""Notifications blueprint — /api/notifications."""

from flask import Blueprint

from app.controllers import notification_controller as ctrl
from app.middleware import ALL_ROLES, roles_required

notification_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notification_bp.get("")
@roles_required(*ALL_ROLES)
def list_notifications():
    return ctrl.get_notifications()


@notification_bp.patch("/read-all")
@roles_required(*ALL_ROLES)
def mark_all_read():
    return ctrl.mark_all_read()


@notification_bp.patch("/<int:notification_id>/read")
@roles_required(*ALL_ROLES)
def mark_read(notification_id):
    return ctrl.mark_read(notification_id)
