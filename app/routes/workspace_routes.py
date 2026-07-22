"""Workspaces + members blueprint — /api/workspaces (path-scoped auth)."""

from flask import Blueprint

from app.controllers import workspace_controller
from app.middleware import login_required

workspace_bp = Blueprint("workspaces", __name__, url_prefix="/api/workspaces")


@workspace_bp.get("")
@login_required
def get_workspaces():
    return workspace_controller.get_workspaces()


@workspace_bp.post("")
@login_required
def create_workspace():
    return workspace_controller.create_workspace()


@workspace_bp.get("/<int:workspace_id>")
@login_required
def get_workspace(workspace_id):
    return workspace_controller.get_workspace(workspace_id)


@workspace_bp.put("/<int:workspace_id>")
@login_required
def update_workspace(workspace_id):
    return workspace_controller.update_workspace(workspace_id)


@workspace_bp.get("/<int:workspace_id>/members")
@login_required
def get_members(workspace_id):
    return workspace_controller.get_members(workspace_id)


@workspace_bp.post("/<int:workspace_id>/members")
@login_required
def add_member(workspace_id):
    return workspace_controller.add_member(workspace_id)


@workspace_bp.put("/<int:workspace_id>/members/<int:member_id>")
@login_required
def update_member(workspace_id, member_id):
    return workspace_controller.update_member(workspace_id, member_id)


@workspace_bp.delete("/<int:workspace_id>/members/<int:member_id>")
@login_required
def remove_member(workspace_id, member_id):
    return workspace_controller.remove_member(workspace_id, member_id)
