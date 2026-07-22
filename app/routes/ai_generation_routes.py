"""AI generations history blueprint — /api/ai-generations."""

from flask import Blueprint

from app.controllers import ai_generation_controller as ctrl
from app.middleware import ALL_ROLES, EDITOR_ROLES, roles_required

ai_generation_bp = Blueprint(
    "ai_generations", __name__, url_prefix="/api/ai-generations"
)


@ai_generation_bp.get("")
@roles_required(*ALL_ROLES)
def list_generations():
    return ctrl.get_ai_generations()


@ai_generation_bp.get("/<int:generation_id>")
@roles_required(*ALL_ROLES)
def get_generation(generation_id):
    return ctrl.get_ai_generation(generation_id)


@ai_generation_bp.delete("/<int:generation_id>")
@roles_required(*EDITOR_ROLES)
def delete_generation(generation_id):
    return ctrl.delete_ai_generation(generation_id)
