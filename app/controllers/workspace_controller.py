"""Workspace + membership management.

Workspace routes are path-scoped (``/api/workspaces/<id>/...``) so membership
and role are resolved from the URL rather than the ``X-Workspace-Id`` header.
"""

import secrets

from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models.notification_model import Notification
from app.models.subscription_model import Subscription
from app.models.user_model import User
from app.models.workspace_member_model import ROLES, WorkspaceMember
from app.models.workspace_model import Workspace
from app.utils import is_valid_email, slugify, utc_now


def generate_unique_workspace_slug(name: str) -> str:
    base = slugify(name)
    slug = base
    counter = 2
    while Workspace.query.filter_by(slug=slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _get_membership(workspace_id: int, user_id: int | None = None):
    return WorkspaceMember.query.filter_by(
        workspace_id=workspace_id, user_id=user_id or current_user.id
    ).first()


def _load_workspace_for_member(workspace_id: int, required_roles: tuple | None = None):
    """Return ``(workspace, None)`` or ``(None, error_response)``."""
    workspace = Workspace.query.get(workspace_id)
    if workspace is None:
        return None, (jsonify({"error": "Workspace not found."}), 404)
    if current_user.is_platform_admin:
        return workspace, None
    member = _get_membership(workspace_id)
    if member is None:
        return None, (jsonify({"error": "You are not a member of this workspace."}), 403)
    if required_roles and member.role not in required_roles:
        return None, (jsonify({"error": "Insufficient role for this action."}), 403)
    return workspace, None


def get_workspaces():
    memberships = (
        WorkspaceMember.query.filter_by(user_id=current_user.id)
        .order_by(WorkspaceMember.id.asc())
        .all()
    )
    workspaces = [{**m.workspace.to_dict(), "role": m.role} for m in memberships]
    return jsonify({"workspaces": workspaces}), 200


def create_workspace():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"errors": ["Workspace name is required."]}), 400
    try:
        workspace = Workspace(
            name=name,
            slug=generate_unique_workspace_slug(name),
            plan_tier="free",
            is_agency=bool(data.get("is_agency", False)),
        )
        db.session.add(workspace)
        db.session.flush()
        db.session.add(
            WorkspaceMember(
                user_id=current_user.id,
                workspace_id=workspace.id,
                role="owner",
                joined_at=utc_now(),
            )
        )
        db.session.add(
            Subscription(workspace_id=workspace.id, plan_tier="free", status="active")
        )
        db.session.commit()
        return jsonify({"message": "Workspace created.", "workspace": workspace.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not create workspace."}), 500


def get_workspace(workspace_id: int):
    workspace, err = _load_workspace_for_member(workspace_id)
    if err:
        return err
    return jsonify({"workspace": workspace.to_dict()}), 200


def update_workspace(workspace_id: int):
    workspace, err = _load_workspace_for_member(workspace_id, ("owner",))
    if err:
        return err
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"errors": ["Name cannot be empty."]}), 400
        workspace.name = name
    if "is_agency" in data:
        workspace.is_agency = bool(data["is_agency"])
    if data.get("slug"):
        new_slug = slugify(data["slug"])
        clash = Workspace.query.filter_by(slug=new_slug).first()
        if clash and clash.id != workspace.id:
            return jsonify({"error": "Slug already in use."}), 409
        workspace.slug = new_slug
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Workspace update failed."}), 500
    return jsonify({"message": "Workspace updated.", "workspace": workspace.to_dict()}), 200


def get_members(workspace_id: int):
    workspace, err = _load_workspace_for_member(workspace_id)
    if err:
        return err
    members = (
        WorkspaceMember.query.filter_by(workspace_id=workspace_id)
        .order_by(WorkspaceMember.id.asc())
        .all()
    )
    return jsonify({"members": [m.to_dict() for m in members]}), 200


def add_member(workspace_id: int):
    workspace, err = _load_workspace_for_member(workspace_id, ("owner",))
    if err:
        return err
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    role = data.get("role") or "editor"
    errors = []
    if not is_valid_email(email):
        errors.append("A valid email is required.")
    if role not in ROLES:
        errors.append(f"Role must be one of: {', '.join(ROLES)}.")
    if errors:
        return jsonify({"errors": errors}), 400
    try:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(email=email, full_name=email.split("@")[0])
            user.set_password(secrets.token_urlsafe(16))
            db.session.add(user)
            db.session.flush()
        if _get_membership(workspace_id, user.id):
            return jsonify({"error": "User is already a member of this workspace."}), 409
        member = WorkspaceMember(
            user_id=user.id, workspace_id=workspace_id, role=role
        )
        db.session.add(member)
        db.session.add(
            Notification(
                user_id=user.id,
                workspace_id=workspace_id,
                type="team_invite",
                message=f"You've been invited to {workspace.name} as {role}.",
            )
        )
        db.session.commit()
        return jsonify({"message": "Member invited.", "member": member.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not invite member."}), 500


def update_member(workspace_id: int, member_id: int):
    workspace, err = _load_workspace_for_member(workspace_id, ("owner",))
    if err:
        return err
    member = WorkspaceMember.query.filter_by(
        id=member_id, workspace_id=workspace_id
    ).first()
    if member is None:
        return jsonify({"error": "Member not found."}), 404
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if role not in ROLES:
        return jsonify({"errors": [f"Role must be one of: {', '.join(ROLES)}."]}), 400
    if member.role == "owner" and role != "owner" and _owner_count(workspace_id) <= 1:
        return jsonify({"error": "Cannot demote the last owner."}), 400
    member.role = role
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not update member."}), 500
    return jsonify({"message": "Member role updated.", "member": member.to_dict()}), 200


def remove_member(workspace_id: int, member_id: int):
    workspace, err = _load_workspace_for_member(workspace_id, ("owner",))
    if err:
        return err
    member = WorkspaceMember.query.filter_by(
        id=member_id, workspace_id=workspace_id
    ).first()
    if member is None:
        return jsonify({"error": "Member not found."}), 404
    if member.role == "owner" and _owner_count(workspace_id) <= 1:
        return jsonify({"error": "Cannot remove the last owner."}), 400
    try:
        db.session.delete(member)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not remove member."}), 500
    return jsonify({"message": "Member removed."}), 200


def _owner_count(workspace_id: int) -> int:
    return WorkspaceMember.query.filter_by(
        workspace_id=workspace_id, role="owner"
    ).count()
