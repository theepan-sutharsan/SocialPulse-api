"""Authentication, role and multi-tenant workspace-isolation middleware.

Two decorators are exported:

* :func:`roles_required` — verifies the JWT, loads the current user, resolves
  the active workspace from the ``X-Workspace-Id`` header, checks the caller's
  membership role, and stores both on ``flask.g``.
* :func:`workspace_scoped` — lightweight guard that only requires a resolved
  workspace context (no specific role), so controllers can safely filter every
  query by ``current_workspace.id``.

``current_workspace`` / ``current_member`` are exposed as ``LocalProxy`` objects
mirroring flask_jwt_extended's ``current_user`` ergonomics.
"""

from functools import wraps

from flask import g, jsonify, request
from flask_jwt_extended import current_user, verify_jwt_in_request
from werkzeug.local import LocalProxy

# Role sets reused across route definitions.
ALL_ROLES = ("owner", "editor", "viewer")
EDITOR_ROLES = ("owner", "editor")
OWNER_ONLY = ("owner",)

current_workspace = LocalProxy(lambda: getattr(g, "current_workspace", None))
current_member = LocalProxy(lambda: getattr(g, "current_member", None))


def _resolve_workspace(user):
    """Resolve the active workspace from ``X-Workspace-Id`` (falls back to the
    user's first membership) and validate the user belongs to it."""
    from app.models.workspace_member_model import WorkspaceMember
    from app.models.workspace_model import Workspace

    raw = request.headers.get("X-Workspace-Id")
    workspace_id = None
    if raw:
        try:
            workspace_id = int(raw)
        except (TypeError, ValueError):
            return None, None, ("Invalid X-Workspace-Id header.", 400)

    if workspace_id is None:
        member = (
            WorkspaceMember.query.filter_by(user_id=user.id)
            .order_by(WorkspaceMember.id.asc())
            .first()
        )
        if member is None:
            return None, None, ("No workspace context available.", 400)
        return member.workspace, member, None

    workspace = Workspace.query.get(workspace_id)
    if workspace is None:
        return None, None, ("Workspace not found.", 404)

    member = WorkspaceMember.query.filter_by(
        user_id=user.id, workspace_id=workspace_id
    ).first()
    if member is None and not user.is_platform_admin:
        return None, None, ("You are not a member of this workspace.", 403)
    return workspace, member, None


def roles_required(*roles):
    """Protect a route: valid JWT + workspace membership with one of ``roles``.

    Passing ``"platform_admin"`` grants access to users with
    ``is_platform_admin`` regardless of workspace membership.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user
            if user is None:
                return jsonify({"error": "Authentication required."}), 401
            if not user.is_active:
                return jsonify({"error": "Account is disabled."}), 403

            wants_admin = "platform_admin" in roles
            workspace_roles = tuple(r for r in roles if r != "platform_admin")

            # Pure platform-admin endpoints: no workspace context needed.
            if wants_admin and not workspace_roles:
                if user.is_platform_admin:
                    return fn(*args, **kwargs)
                return jsonify({"error": "Platform admin access required."}), 403

            workspace, member, err = _resolve_workspace(user)
            if err is not None:
                message, status = err
                return jsonify({"error": message}), status

            g.current_workspace = workspace
            g.current_member = member

            # Platform admins bypass workspace role checks.
            if user.is_platform_admin:
                return fn(*args, **kwargs)

            if workspace_roles and (member is None or member.role not in workspace_roles):
                return jsonify(
                    {"error": "Insufficient role for this action."}
                ), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def workspace_scoped(fn):
    """Require a resolved workspace context without enforcing a specific role."""

    @wraps(fn)
    @roles_required(*ALL_ROLES)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def login_required(fn):
    """Require a valid JWT + active user, without any workspace context.

    Used by path-scoped routes (e.g. ``/api/workspaces/<id>``) that resolve and
    authorize the target workspace from the URL rather than the header.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if current_user is None:
            return jsonify({"error": "Authentication required."}), 401
        if not current_user.is_active:
            return jsonify({"error": "Account is disabled."}), 403
        return fn(*args, **kwargs)

    return wrapper
