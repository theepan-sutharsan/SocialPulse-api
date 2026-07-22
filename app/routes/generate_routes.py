"""AI generation blueprint — /api/generate (credit-gated, Editor/Owner)."""

from flask import Blueprint

from app.controllers import ai_generation_controller as ctrl
from app.middleware import EDITOR_ROLES, roles_required

generate_bp = Blueprint("generate", __name__, url_prefix="/api/generate")


@generate_bp.post("/caption")
@roles_required(*EDITOR_ROLES)
def caption():
    return ctrl.generate_caption()


@generate_bp.post("/hashtags")
@roles_required(*EDITOR_ROLES)
def hashtags():
    return ctrl.generate_hashtags()


@generate_bp.post("/content-idea")
@roles_required(*EDITOR_ROLES)
def content_idea():
    return ctrl.generate_content_idea()


@generate_bp.post("/viral-score")
@roles_required(*EDITOR_ROLES)
def viral_score():
    return ctrl.generate_viral_score()


@generate_bp.post("/sentiment")
@roles_required(*EDITOR_ROLES)
def sentiment():
    return ctrl.generate_sentiment()
