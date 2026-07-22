"""Authentication: register (creates workspace + owner membership), login,
logout, and profile read/update.
"""

from flask import jsonify, request
from flask_jwt_extended import create_access_token, current_user

from app.controllers.credit_usage_controller import get_or_create_current_usage
from app.controllers.workspace_controller import generate_unique_workspace_slug
from app.extensions import db
from app.models.subscription_model import Subscription
from app.models.user_model import User
from app.models.workspace_member_model import WorkspaceMember
from app.models.workspace_model import Workspace
from app.utils import is_valid_email, utc_now


def _validate_register_payload(data: dict) -> list[str]:
    errors = []
    if not is_valid_email((data.get("email") or "").strip()):
        errors.append("A valid email is required.")
    if len(data.get("password") or "") < 8:
        errors.append("Password must be at least 8 characters.")
    if not (data.get("full_name") or "").strip():
        errors.append("Full name is required.")
    return errors


def register():
    data = request.get_json(silent=True) or {}
    errors = _validate_register_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered."}), 409

    try:
        user = User(email=email, full_name=data["full_name"].strip())
        user.set_password(data["password"])
        db.session.add(user)
        db.session.flush()

        workspace_name = (
            data.get("workspace_name") or f"{user.full_name}'s Workspace"
        ).strip()
        workspace = Workspace(
            name=workspace_name,
            slug=generate_unique_workspace_slug(workspace_name),
            plan_tier="free",
        )
        db.session.add(workspace)
        db.session.flush()

        db.session.add(
            WorkspaceMember(
                user_id=user.id,
                workspace_id=workspace.id,
                role="owner",
                joined_at=utc_now(),
            )
        )
        db.session.add(
            Subscription(workspace_id=workspace.id, plan_tier="free", status="active")
        )
        db.session.commit()

        # Seed the free-tier monthly credit pool (5 credits).
        get_or_create_current_usage(workspace)

        token = create_access_token(identity=user)
        return (
            jsonify(
                {
                    "message": "Registration successful.",
                    "access_token": token,
                    "user": user.to_dict(),
                    "workspaces": user.workspaces_payload(),
                }
            ),
            201,
        )
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Registration failed. Please try again."}), 500


def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401
    if not user.is_active:
        return jsonify({"error": "Account is disabled."}), 403

    token = create_access_token(identity=user)
    return (
        jsonify(
            {
                "message": "Login successful.",
                "access_token": token,
                "user": user.to_dict(),
                "workspaces": user.workspaces_payload(),
            }
        ),
        200,
    )


def logout():
    # Stateless JWT: the client discards the token. Endpoint kept for symmetry.
    return jsonify({"message": "Logged out successfully."}), 200


def get_profile():
    return (
        jsonify(
            {
                "user": current_user.to_dict(),
                "workspaces": current_user.workspaces_payload(),
            }
        ),
        200,
    )


def update_profile():
    data = request.get_json(silent=True) or {}
    errors = []
    if "full_name" in data and not (data.get("full_name") or "").strip():
        errors.append("Full name cannot be empty.")
    if data.get("password") and len(data["password"]) < 8:
        errors.append("Password must be at least 8 characters.")
    if errors:
        return jsonify({"errors": errors}), 400

    user = current_user
    if "full_name" in data:
        user.full_name = data["full_name"].strip()
    if data.get("password"):
        user.set_password(data["password"])
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Profile update failed."}), 500
    return jsonify({"message": "Profile updated.", "user": user.to_dict()}), 200
