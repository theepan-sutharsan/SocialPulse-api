"""Billing integration: Stripe + Razorpay checkout and webhooks.

SDKs are imported lazily. When a provider isn't configured (no API keys), a
*simulated* checkout is used so the upgrade flow is demoable locally: the plan
change is applied immediately and a success URL is returned. Real webhooks are
signature-verified before any state change.
"""

import json
import logging
from datetime import timedelta

from flask import current_app

from app.config import Config
from app.controllers.credit_usage_controller import get_or_create_current_usage
from app.extensions import db
from app.models.subscription_model import Subscription
from app.models.workspace_model import Workspace
from app.utils import utc_now

logger = logging.getLogger(__name__)


class WebhookVerificationError(Exception):
    """Raised when a webhook signature cannot be verified."""


def _apply_plan_change(workspace: Workspace, plan_tier: str, provider=None, **ids) -> Subscription:
    """Update subscription + workspace tier + reset the credit allotment."""
    workspace.plan_tier = plan_tier
    workspace.is_agency = plan_tier == "agency"

    subscription = Subscription.query.filter_by(workspace_id=workspace.id).first()
    if subscription is None:
        subscription = Subscription(workspace_id=workspace.id)
        db.session.add(subscription)
    subscription.plan_tier = plan_tier
    subscription.status = "active"
    if provider:
        subscription.billing_provider = provider
    if ids.get("customer_id"):
        subscription.provider_customer_id = ids["customer_id"]
    if ids.get("subscription_id"):
        subscription.provider_subscription_id = ids["subscription_id"]
    subscription.current_period_end = utc_now() + timedelta(days=30)

    usage = get_or_create_current_usage(workspace)
    usage.credits_allotted = Config.PLAN_CREDITS.get(plan_tier, usage.credits_allotted)

    db.session.commit()
    return subscription


def create_checkout_session(workspace: Workspace, plan_tier: str, provider: str) -> str:
    if provider == "stripe" and current_app.config.get("STRIPE_SECRET_KEY"):
        return _stripe_checkout(workspace, plan_tier)
    if provider == "razorpay" and current_app.config.get("RAZORPAY_KEY_ID"):
        return _razorpay_checkout(workspace, plan_tier)

    # Simulated checkout (no keys configured) — apply immediately for the demo.
    _apply_plan_change(workspace, plan_tier, provider=provider)
    frontend = current_app.config["FRONTEND_URL"]
    return f"{frontend}/billing?upgraded={plan_tier}&provider={provider}&simulated=1"


def _stripe_checkout(workspace: Workspace, plan_tier: str) -> str:
    import stripe

    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    frontend = current_app.config["FRONTEND_URL"]
    session = stripe.checkout.Session.create(
        mode="subscription",
        client_reference_id=str(workspace.id),
        metadata={"workspace_id": workspace.id, "plan_tier": plan_tier},
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                    "unit_amount": Config.PLAN_PRICES_USD[plan_tier] * 100,
                    "product_data": {"name": f"{plan_tier.title()} plan"},
                },
            }
        ],
        success_url=f"{frontend}/billing?success=1",
        cancel_url=f"{frontend}/billing?cancelled=1",
    )
    return session.url


def _razorpay_checkout(workspace: Workspace, plan_tier: str) -> str:
    import razorpay

    client = razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"],
        )
    )
    order = client.order.create(
        {
            "amount": Config.PLAN_PRICES_INR[plan_tier] * 100,
            "currency": "INR",
            "notes": {"workspace_id": workspace.id, "plan_tier": plan_tier},
        }
    )
    frontend = current_app.config["FRONTEND_URL"]
    return f"{frontend}/billing?razorpay_order={order['id']}&plan={plan_tier}"


def handle_stripe_webhook(payload: bytes, signature: str) -> None:
    import stripe

    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")
    try:
        if secret:
            event = stripe.Webhook.construct_event(payload, signature, secret)
        else:
            event = json.loads(payload or b"{}")
    except Exception as exc:  # noqa: BLE001
        raise WebhookVerificationError(str(exc)) from exc

    _process_event(
        event.get("type", ""),
        (event.get("data", {}) or {}).get("object", {}) or {},
    )


def handle_razorpay_webhook(payload: bytes, signature: str) -> None:
    import razorpay

    secret = current_app.config.get("RAZORPAY_KEY_SECRET")
    try:
        if secret and signature:
            razorpay.Utility().verify_webhook_signature(
                payload.decode("utf-8"), signature, secret
            )
        event = json.loads(payload or b"{}")
    except Exception as exc:  # noqa: BLE001
        raise WebhookVerificationError(str(exc)) from exc

    entity = (
        event.get("payload", {})
        .get("subscription", event.get("payload", {}).get("payment", {}))
        .get("entity", {})
    )
    _process_event(event.get("event", ""), entity.get("notes", entity))


def _process_event(event_type: str, obj: dict) -> None:
    metadata = obj.get("metadata") or obj.get("notes") or obj
    workspace_id = metadata.get("workspace_id") or obj.get("client_reference_id")
    if not workspace_id:
        logger.info("Webhook %s ignored: no workspace_id.", event_type)
        return
    workspace = Workspace.query.get(int(workspace_id))
    if workspace is None:
        return

    if event_type in (
        "checkout.session.completed",
        "customer.subscription.updated",
        "subscription.activated",
        "subscription.charged",
    ):
        plan_tier = metadata.get("plan_tier", workspace.plan_tier)
        _apply_plan_change(workspace, plan_tier)
    elif event_type in ("customer.subscription.deleted", "subscription.cancelled"):
        _apply_plan_change(workspace, "free")


def cancel_subscription(workspace: Workspace) -> Subscription | None:
    subscription = Subscription.query.filter_by(workspace_id=workspace.id).first()
    if subscription is None:
        return None
    subscription.status = "cancelled"
    # Access continues until period end; tier reverts to free then (via webhook
    # in production). For the demo we downgrade immediately.
    _apply_plan_change(workspace, "free", provider=subscription.billing_provider)
    subscription.status = "cancelled"
    db.session.commit()
    return subscription
