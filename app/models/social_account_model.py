"""SocialAccount — a connected (OAuth), publicly-tracked, or demo account.

OAuth tokens are stored encrypted at rest and never serialized. ``source``
records how the account's data is obtained:

* ``demo``   — deterministic mock data (seeded Instagram/TikTok/X channels).
* ``oauth``  — the owner authorized the account; data comes from their token.
* ``public`` — SocialBlade-style tracking of any public channel via the
  YouTube Data API **key** (no login). ``external_id`` holds the channel id so
  daily snapshots can re-fetch real stats. No fabricated history is stored.
"""

from app.extensions import db
from app.utils import iso, utc_now

PLATFORMS = ("youtube", "instagram", "tiktok", "twitter")
SOURCES = ("demo", "oauth", "public")


class SocialAccount(db.Model):
    __tablename__ = "social_accounts"
    __table_args__ = (
        db.UniqueConstraint(
            "workspace_id", "platform", "handle", name="uq_account_ws_platform_handle"
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id = db.Column(
        db.Integer,
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform = db.Column(db.String(20), nullable=False)
    handle = db.Column(db.String(255), nullable=False)
    is_demo = db.Column(db.Boolean, default=True, nullable=False)
    source = db.Column(db.String(20), default="demo", nullable=False)
    # Platform-native identifier (e.g. YouTube channelId) for public tracking.
    external_id = db.Column(db.String(64), nullable=True, index=True)
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
        """OAuth-connected account (owner authorized data access)."""
        return self.source == "oauth"

    @property
    def is_tracked(self) -> bool:
        """Public channel tracked via API key (SocialBlade-style, no OAuth)."""
        return self.source == "public"

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
            "source": self.source,
            "is_demo": self.is_demo,
            "is_connected": self.is_connected,
            "is_tracked": self.is_tracked,
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
