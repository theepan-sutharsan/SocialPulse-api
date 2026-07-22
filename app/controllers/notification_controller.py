"""Per-user, workspace-scoped notification feed."""

from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.middleware import current_workspace
from app.models.notification_model import Notification


def get_notifications():
    query = Notification.query.filter_by(
        user_id=current_user.id, workspace_id=current_workspace.id
    )
    if request.args.get("unread") in ("1", "true", "yes"):
        query = query.filter_by(is_read=False)
    notifications = query.order_by(Notification.created_at.desc()).all()
    unread = sum(1 for n in notifications if not n.is_read)
    return (
        jsonify(
            {
                "notifications": [n.to_dict() for n in notifications],
                "unread_count": unread,
            }
        ),
        200,
    )


def mark_read(notification_id: int):
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id, workspace_id=current_workspace.id
    ).first()
    if notification is None:
        return jsonify({"error": "Notification not found."}), 404
    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Notification marked read.", "notification": notification.to_dict()}), 200


def mark_all_read():
    Notification.query.filter_by(
        user_id=current_user.id, workspace_id=current_workspace.id, is_read=False
    ).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All notifications marked read."}), 200
