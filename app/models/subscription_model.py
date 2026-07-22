"""Subscription — mirrors the Stripe/Razorpay subscription state per workspace."""

from app.extensions import db
from app.utils import iso, utc_now

PLAN_TIERS = ("free", "pro", "agency")
BILLING_PROVIDERS = ("stripe", "razorpay")
STATUSES = ("active", "past_due", "cancelled")


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id = db.Column(
        db.Integer,
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    plan_tier = db.Column(db.String(20), default="free", nullable=False)
    billing_provider = db.Column(db.String(20), nullable=True)
    provider_customer_id = db.Column(db.String(255), nullable=True)
    provider_subscription_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    workspace = db.relationship("Workspace", back_populates="subscription")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "plan_tier": self.plan_tier,
            "billing_provider": self.billing_provider,
            "provider_customer_id": self.provider_customer_id,
            "provider_subscription_id": self.provider_subscription_id,
            "status": self.status,
            "current_period_end": iso(self.current_period_end),
            "created_at": iso(self.created_at),
        }
