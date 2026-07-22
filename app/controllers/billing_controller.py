"""Billing endpoints: plan catalog (public), checkout, signature-verified
webhooks, current subscription, and cancellation. All gateway access goes
through :mod:`app.services.billing_service`.
"""

from flask import jsonify, request

from app.config import Config
from app.middleware import current_workspace
from app.models.subscription_model import BILLING_PROVIDERS, PLAN_TIERS, Subscription
from app.services import billing_service

PLAN_FEATURES = {
    "free": [
        "1 workspace",
        "5 AI credits / month",
        "Demo Mode connections",
        "Basic growth charts",
    ],
    "pro": [
        "Unlimited connections",
        "500 AI credits / month",
        "Full history + grade",
        "CSV & PDF export",
    ],
    "agency": [
        "Everything in Pro",
        "5000 AI credits / month",
        "Multiple client workspaces",
        "White-label media kit",
    ],
}


def get_plans():
    plans = [
        {
            "tier": tier,
            "credits": Config.PLAN_CREDITS[tier],
            "price_usd": Config.PLAN_PRICES_USD[tier],
            "price_inr": Config.PLAN_PRICES_INR[tier],
            "features": PLAN_FEATURES[tier],
        }
        for tier in ("free", "pro", "agency")
    ]
    return jsonify({"plans": plans}), 200


def create_checkout():
    data = request.get_json(silent=True) or {}
    plan_tier = data.get("plan_tier")
    provider = data.get("provider", "stripe")
    errors = []
    if plan_tier not in PLAN_TIERS or plan_tier == "free":
        errors.append("plan_tier must be 'pro' or 'agency'.")
    if provider not in BILLING_PROVIDERS:
        errors.append(f"provider must be one of: {', '.join(BILLING_PROVIDERS)}.")
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        checkout_url = billing_service.create_checkout_session(
            current_workspace, plan_tier, provider
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Could not start checkout: {exc}"}), 502
    return jsonify({"checkout_url": checkout_url, "provider": provider}), 200


def stripe_webhook():
    payload = request.get_data()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        billing_service.handle_stripe_webhook(payload, signature)
    except billing_service.WebhookVerificationError:
        return jsonify({"error": "Invalid webhook signature."}), 400
    except Exception:  # noqa: BLE001
        return jsonify({"error": "Webhook processing failed."}), 400
    return jsonify({"received": True}), 200


def razorpay_webhook():
    payload = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "")
    try:
        billing_service.handle_razorpay_webhook(payload, signature)
    except billing_service.WebhookVerificationError:
        return jsonify({"error": "Invalid webhook signature."}), 400
    except Exception:  # noqa: BLE001
        return jsonify({"error": "Webhook processing failed."}), 400
    return jsonify({"received": True}), 200


def get_subscription():
    subscription = Subscription.query.filter_by(
        workspace_id=current_workspace.id
    ).first()
    if subscription is None:
        return jsonify({"subscription": None}), 200
    return jsonify({"subscription": subscription.to_dict()}), 200


def cancel_subscription():
    try:
        subscription = billing_service.cancel_subscription(current_workspace)
    except Exception:  # noqa: BLE001
        return jsonify({"error": "Could not cancel subscription."}), 502
    return (
        jsonify(
            {
                "message": "Subscription cancelled. Access continues until period end.",
                "subscription": subscription.to_dict() if subscription else None,
            }
        ),
        200,
    )
