"""Webhook controller for Instagram and external platform events."""

import logging
from flask import Response, current_app, jsonify, request

logger = logging.getLogger(__name__)


def verify_instagram_webhook():
    """Verify Instagram Webhook setup from Meta Developer Dashboard (GET).

    Meta sends query parameters:
    - hub.mode
    - hub.verify_token
    - hub.challenge

    Verification:
    Compare hub.verify_token with INSTAGRAM_VERIFY_TOKEN env variable.
    If valid: return hub.challenge with HTTP 200.
    Otherwise: return HTTP 403.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    expected_token = current_app.config.get("INSTAGRAM_VERIFY_TOKEN", "")

    if not expected_token:
        logger.warning("INSTAGRAM_VERIFY_TOKEN is not configured on the server.")
        return jsonify({"error": "INSTAGRAM_VERIFY_TOKEN is not configured."}), 403

    if mode == "subscribe" and token == expected_token:
        logger.info("Instagram webhook challenge verified successfully.")
        return Response(challenge or "", status=200, mimetype="text/plain")

    logger.warning(
        "Instagram webhook verification failed. Invalid token or mode: mode=%s", mode
    )
    return jsonify({"error": "Verification failed. Invalid verify token."}), 403


def handle_instagram_webhook():
    """Receive and log incoming Instagram webhook event notifications (POST)."""
    try:
        payload = request.get_json(silent=True)
        if payload is None:
            payload = request.get_data(as_text=True)
        logger.info("Received Instagram webhook payload: %s", payload)

        return jsonify({"status": "ok", "message": "EVENT_RECEIVED"}), 200
    except Exception as exc:
        logger.error("Error processing Instagram webhook event: %s", exc, exc_info=True)
        return jsonify({"error": "Failed to process webhook event."}), 500
