"""AnalyticsSnapshot — daily time-series row per social account.

SIGNATURE table. One row per account per day (unique on
``social_account_id + snapshot_date``) powering SocialBlade-style growth charts,
milestone projection, and the composite grade without hitting live APIs on every
dashboard load.
"""

from app.extensions import db
from app.utils import iso, utc_now


class AnalyticsSnapshot(db.Model):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        db.UniqueConstraint(
            "social_account_id", "snapshot_date", name="uq_snapshot_account_date"
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    social_account_id = db.Column(
        db.Integer,
        db.ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_date = db.Column(db.Date, nullable=False)
    follower_count = db.Column(db.Integer, default=0, nullable=False)
    view_count = db.Column(db.BigInteger, default=0, nullable=False)
    engagement_rate = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    social_account = db.relationship("SocialAccount", back_populates="snapshots")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "social_account_id": self.social_account_id,
            "snapshot_date": iso(self.snapshot_date),
            "follower_count": self.follower_count,
            "view_count": self.view_count,
            "engagement_rate": (
                float(self.engagement_rate) if self.engagement_rate is not None else 0.0
            ),
            "created_at": iso(self.created_at),
        }
