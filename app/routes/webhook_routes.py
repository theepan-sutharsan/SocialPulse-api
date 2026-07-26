"""Webhook routes blueprint — /api/webhook."""

from flask import Blueprint

from app.controllers import webhook_controller as ctrl

webhook_bp = Blueprint("webhook", __name__, url_prefix="/api/webhook")


@webhook_bp.get("/instagram")
def verify_instagram_webhook():
    return ctrl.verify_instagram_webhook()


@webhook_bp.post("/instagram")
def handle_instagram_webhook():
    return ctrl.handle_instagram_webhook()
