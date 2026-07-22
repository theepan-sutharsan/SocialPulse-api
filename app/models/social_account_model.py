"""SocialAccount — a connected (live) or demo social platform account.

OAuth tokens are stored encrypted at rest and never serialized. ``is_demo`` is
True for seeded Instagram/TikTok/X accounts until live OAuth is available.
"""

from app.extensions import db
from app.utils import iso, utc_now

PLATFORMS = ("youtube", "instagram", "tiktok", "twitter")


class SocialAccount(db.Model):
    __tablename__ = "social_accounts"
    __table_args__ = (
        db.UniqueConstraint(
            "workspace_id", "platform", "handle", name="uq_account_ws_platform_handle"
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id = db.Column(
        db.Integer, db.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    platform = db.Column(db.String(20), nullable=False)
    handle = db.Column(db.String(255), nullable=False)
    is_demo = db.Column(db.Boolean, default=True, nullable=False)
    access_token = db.Column(db.Text, nullable=True)  # encrypted
    refresh_token = db.Column(db.Text, nullable=True)  # encrypted
    connected_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    workspace = db.relationship("Workspace", back_populates="social_accounts")
    snapshots = db.relationship(
        "AnalyticsSnapshot",
        back_populates="social_account",
        cascade="all, delete-orphan",
        order_by="AnalyticsSnapshot.snapshot_date",
    )

    @property
    def is_connected(self) -> bool:
        return bool(self.access_token) and not self.is_demo

    def latest_snapshot(self):
        return self.snapshots[-1] if self.snapshots else None

    def __repr__(self) -> str:
        return f"<SocialAccount {self.id} {self.platform}:{self.handle}>"

    def to_dict(self) -> dict:
        latest = self.latest_snapshot()
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "platform": self.platform,
            "handle": self.handle,
            "is_demo": self.is_demo,
            "is_connected": self.is_connected,
            "connected_at": iso(self.connected_at),
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
            "follower_count": latest.follower_count if latest else 0,
            "view_count": latest.view_count if latest else 0,
            "engagement_rate": (
                float(latest.engagement_rate)
                if latest and latest.engagement_rate is not None
                else 0.0
            ),
        }
