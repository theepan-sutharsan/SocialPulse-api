"""Referral — stretch feature: bonus AI credits for referrer + referee."""

from app.extensions import db
from app.utils import iso, utc_now

STATUSES = ("pending", "joined", "credited")


class Referral(db.Model):
    __tablename__ = "referrals"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    referrer_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    referred_email = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    referrer = db.relationship("User")

    def __repr__(self) -> str:
        return f"<Referral {self.id} {self.status}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "referrer_id": self.referrer_id,
            "referred_email": self.referred_email,
            "status": self.status,
            "created_at": iso(self.created_at),
        }
