"""Scheduled posts (planning only in v1): create, list, detail, edit, cancel."""

from flask import jsonify, request

from app.extensions import db
from app.middleware import current_workspace
from app.models.ai_generation_model import AIGeneration
from app.models.scheduled_post_model import STATUSES, ScheduledPost
from app.models.social_account_model import SocialAccount
from app.utils import parse_datetime


def _validate_payload(data: dict, require_all: bool = True) -> list[str]:
    errors = []
    if require_all or "caption" in data:
        if not (data.get("caption") or "").strip():
            errors.append("Caption is required.")
    if require_all or "scheduled_at" in data:
        try:
            if parse_datetime(data.get("scheduled_at")) is None:
                errors.append("A valid scheduled_at datetime is required.")
        except (ValueError, TypeError):
            errors.append("scheduled_at must be an ISO-8601 datetime.")
    if require_all and not data.get("social_account_id"):
        errors.append("social_account_id is required.")
    return errors


def _account_in_workspace(account_id):
    return SocialAccount.query.filter_by(
        id=account_id, workspace_id=current_workspace.id
    ).first()


def create_scheduled_post():
    data = request.get_json(silent=True) or {}
    errors = _validate_payload(data, require_all=True)
    if errors:
        return jsonify({"errors": errors}), 400

    account = _account_in_workspace(data.get("social_account_id"))
    if account is None:
        return jsonify({"error": "Social account not found."}), 404

    generation_id = data.get("ai_generation_id")
    if generation_id and not AIGeneration.query.filter_by(
        id=generation_id, workspace_id=current_workspace.id
    ).first():
        return jsonify({"error": "AI generation not found."}), 404

    try:
        post = ScheduledPost(
            workspace_id=current_workspace.id,
            ai_generation_id=generation_id,
            social_account_id=account.id,
            caption=data["caption"].strip(),
            scheduled_at=parse_datetime(data["scheduled_at"]),
            status="planned",
        )
        db.session.add(post)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not schedule post."}), 500
    return jsonify({"message": "Post scheduled.", "scheduled_post": post.to_dict()}), 201


def get_scheduled_posts():
    query = ScheduledPost.query.filter_by(workspace_id=current_workspace.id)
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)
    from_dt = parse_datetime(request.args.get("from")) if request.args.get("from") else None
    to_dt = parse_datetime(request.args.get("to")) if request.args.get("to") else None
    if from_dt:
        query = query.filter(ScheduledPost.scheduled_at >= from_dt)
    if to_dt:
        query = query.filter(ScheduledPost.scheduled_at <= to_dt)
    posts = query.order_by(ScheduledPost.scheduled_at.asc()).all()
    return jsonify({"scheduled_posts": [p.to_dict() for p in posts]}), 200


def _get_post_or_none(post_id):
    return ScheduledPost.query.filter_by(
        id=post_id, workspace_id=current_workspace.id
    ).first()


def get_scheduled_post(post_id: int):
    post = _get_post_or_none(post_id)
    if post is None:
        return jsonify({"error": "Scheduled post not found."}), 404
    return jsonify({"scheduled_post": post.to_dict()}), 200


def update_scheduled_post(post_id: int):
    post = _get_post_or_none(post_id)
    if post is None:
        return jsonify({"error": "Scheduled post not found."}), 404
    data = request.get_json(silent=True) or {}
    errors = _validate_payload(data, require_all=False)
    if errors:
        return jsonify({"errors": errors}), 400

    if "caption" in data:
        post.caption = data["caption"].strip()
    if "scheduled_at" in data:
        post.scheduled_at = parse_datetime(data["scheduled_at"])
    if data.get("social_account_id"):
        account = _account_in_workspace(data["social_account_id"])
        if account is None:
            return jsonify({"error": "Social account not found."}), 404
        post.social_account_id = account.id
    if data.get("status") in STATUSES:
        post.status = data["status"]
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not update scheduled post."}), 500
    return jsonify({"message": "Scheduled post updated.", "scheduled_post": post.to_dict()}), 200


def cancel_scheduled_post(post_id: int):
    post = _get_post_or_none(post_id)
    if post is None:
        return jsonify({"error": "Scheduled post not found."}), 404
    post.status = "cancelled"
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not cancel scheduled post."}), 500
    return jsonify({"message": "Scheduled post cancelled.", "scheduled_post": post.to_dict()}), 200
