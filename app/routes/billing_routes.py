"""Billing blueprint — /api/billing.

Webhook endpoints are authenticated by provider signature (no JWT).
"""

from flask import Blueprint

from app.controllers import billing_controller as ctrl
from app.middleware import OWNER_ONLY, roles_required

billing_bp = Blueprint("billing", __name__, url_prefix="/api/billing")


@billing_bp.get("/plans")
def plans():
    return ctrl.get_plans()


@billing_bp.post("/checkout")
@roles_required(*OWNER_ONLY)
def checkout():
    return ctrl.create_checkout()


@billing_bp.post("/webhook/stripe")
def stripe_webhook():
    return ctrl.stripe_webhook()


@billing_bp.post("/webhook/razorpay")
def razorpay_webhook():
    return ctrl.razorpay_webhook()


@billing_bp.get("/subscription")
@roles_required(*OWNER_ONLY)
def subscription():
    return ctrl.get_subscription()


@billing_bp.post("/cancel")
@roles_required(*OWNER_ONLY)
def cancel():
    return ctrl.cancel_subscription()
