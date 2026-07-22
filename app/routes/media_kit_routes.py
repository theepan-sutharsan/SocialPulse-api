"""Media kit blueprint — /api/media-kit (public GET, Owner/Editor PUT)."""

from flask import Blueprint

from app.controllers import media_kit_controller as ctrl
from app.middleware import EDITOR_ROLES, roles_required

media_kit_bp = Blueprint("media_kit", __name__, url_prefix="/api/media-kit")


@media_kit_bp.get("/<workspace_slug>")
def get_media_kit(workspace_slug):
    return ctrl.get_media_kit(workspace_slug)


@media_kit_bp.put("")
@roles_required(*EDITOR_ROLES)
def update_media_kit():
    return ctrl.update_media_kit()
