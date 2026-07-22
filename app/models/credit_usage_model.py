"""CreditUsage — the monthly AI-credit ledger per workspace."""

from app.extensions import db
from app.utils import iso, utc_now


class CreditUsage(db.Model):
    __tablename__ = "credit_usages"
    __table_args__ = (
        db.UniqueConstraint(
            "workspace_id", "period_start", name="uq_credit_ws_period"
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id = db.Column(
        db.Integer, db.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    period_start = db.Column(db.Date, nullable=False)
    credits_allotted = db.Column(db.Integer, default=0, nullable=False)
    credits_used = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    workspace = db.relationship("Workspace", back_populates="credit_usages")

    @property
    def credits_remaining(self) -> int:
        return max(self.credits_allotted - self.credits_used, 0)

    def __repr__(self) -> str:
        return f"<CreditUsage ws{self.workspace_id} {self.credits_used}/{self.credits_allotted}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "period_start": iso(self.period_start),
            "credits_allotted": self.credits_allotted,
            "credits_used": self.credits_used,
            "credits_remaining": self.credits_remaining,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
