"""AI generation endpoints.

Every ``/api/generate/*`` call is credit-gated: a cache miss with no remaining
credits returns ``402`` before any provider call. Credits are deducted only on a
successful, non-cached generation (cached hits are billed once, served many).
All provider access goes through :mod:`app.services.ai_service`.
"""

from flask import jsonify, request

from app.controllers.credit_usage_controller import (
    consume_credits,
    get_or_create_current_usage,
    has_available_credits,
)
from app.extensions import db
from app.middleware import current_workspace
from app.models.ai_generation_model import GENERATION_TYPES, AIGeneration
from app.models.social_account_model import SocialAccount
from app.services import ai_service


def _resolve_account(social_account_id):
    if not social_account_id:
        return None, None
    account = SocialAccount.query.filter_by(
        id=social_account_id, workspace_id=current_workspace.id
    ).first()
    if account is None:
        return None, (jsonify({"error": "Social account not found."}), 404)
    return account, None


def _run_generation(generation_type: str, prompt_input: str, social_account_id=None):
    account, err = _resolve_account(social_account_id)
    if err:
        return err

    workspace = current_workspace
    # Cache-aware credit gate: never call the provider with no credits.
    is_cached = ai_service.peek_cache(generation_type, prompt_input) is not None
    if not is_cached and not has_available_credits(workspace, 1):
        return jsonify({"error": "AI credit limit reached. Upgrade your plan."}), 402

    try:
        result = ai_service.generate(generation_type, prompt_input, workspace, account)
    except ai_service.AIGenerationError:
        return jsonify({"error": "AI generation failed."}), 502

    credits_used = 0 if result["cached"] else 1
    try:
        if not result["cached"]:
            consume_credits(workspace, 1)
        generation = AIGeneration(
            workspace_id=workspace.id,
            social_account_id=account.id if account else None,
            generation_type=generation_type,
            prompt_input=prompt_input,
            result=result["result"],
            provider=result["provider"],
            credits_used=credits_used,
        )
        db.session.add(generation)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not persist generation."}), 500

    return (
        jsonify(
            {
                "message": "Generation complete.",
                "ai_generation": generation.to_dict(),
                "credit_usage": get_or_create_current_usage(workspace).to_dict(),
            }
        ),
        201,
    )


def generate_caption():
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    if not topic:
        return jsonify({"errors": ["A topic is required."]}), 400
    platform = (data.get("platform") or "instagram").strip()
    tone = (data.get("tone") or "engaging").strip()
    prompt_input = f"Topic: {topic}\nPlatform: {platform}\nTone: {tone}"
    return _run_generation("caption", prompt_input, data.get("social_account_id"))


def generate_hashtags():
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    if not topic:
        return jsonify({"errors": ["A topic is required."]}), 400
    platform = (data.get("platform") or "instagram").strip()
    prompt_input = f"Topic: {topic}\nPlatform: {platform}"
    return _run_generation("hashtags", prompt_input, data.get("social_account_id"))


def generate_content_idea():
    data = request.get_json(silent=True) or {}
    niche = (data.get("niche") or data.get("topic") or "").strip()
    if not niche:
        return jsonify({"errors": ["A niche or topic is required."]}), 400
    prompt_input = f"Niche: {niche}"
    return _run_generation("content_idea", prompt_input, data.get("social_account_id"))


def generate_viral_score():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or data.get("draft") or "").strip()
    if not text:
        return jsonify({"errors": ["Draft post text is required."]}), 400
    return _run_generation("viral_score", text, data.get("social_account_id"))


def generate_sentiment():
    data = request.get_json(silent=True) or {}
    social_account_id = data.get("social_account_id")
    if not social_account_id:
        return jsonify({"errors": ["A social_account_id is required."]}), 400
    account, err = _resolve_account(social_account_id)
    if err:
        return err
    prompt_input = f"Sentiment analysis for {account.platform} @{account.handle}"
    return _run_generation("sentiment", prompt_input, social_account_id)


def get_ai_generations():
    query = AIGeneration.query.filter_by(workspace_id=current_workspace.id)
    gen_type = request.args.get("type")
    if gen_type:
        query = query.filter_by(generation_type=gen_type)
    account_id = request.args.get("social_account_id")
    if account_id:
        query = query.filter_by(social_account_id=account_id)
    generations = query.order_by(AIGeneration.created_at.desc()).all()
    return jsonify({"ai_generations": [g.to_dict() for g in generations]}), 200


def get_ai_generation(generation_id: int):
    generation = AIGeneration.query.filter_by(
        id=generation_id, workspace_id=current_workspace.id
    ).first()
    if generation is None:
        return jsonify({"error": "AI generation not found."}), 404
    return jsonify({"ai_generation": generation.to_dict()}), 200


def delete_ai_generation(generation_id: int):
    generation = AIGeneration.query.filter_by(
        id=generation_id, workspace_id=current_workspace.id
    ).first()
    if generation is None:
        return jsonify({"error": "AI generation not found."}), 404
    try:
        db.session.delete(generation)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not delete generation."}), 500
    return jsonify({"message": "AI generation deleted."}), 200
