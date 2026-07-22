"""Platform admin blueprint — /api/platform-admin (platform_admin only)."""

from flask import Blueprint

from app.controllers import platform_admin_controller as ctrl
from app.middleware import roles_required

platform_admin_bp = Blueprint(
    "platform_admin", __name__, url_prefix="/api/platform-admin"
)


@platform_admin_bp.get("/workspaces")
@roles_required("platform_admin")
def list_workspaces():
    return ctrl.list_workspaces()


@platform_admin_bp.get("/workspaces/<int:workspace_id>")
@roles_required("platform_admin")
def get_workspace(workspace_id):
    return ctrl.get_workspace(workspace_id)


@platform_admin_bp.patch("/workspaces/<int:workspace_id>/plan")
@roles_required("platform_admin")
def update_plan(workspace_id):
    return ctrl.update_plan(workspace_id)
