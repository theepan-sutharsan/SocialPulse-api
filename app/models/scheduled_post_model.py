"""ScheduledPost — plans an AI-generated piece of content for a future date.

Scheduling only in v1 (no publish automation).
"""

from app.extensions import db
from app.utils import iso, utc_now

STATUSES = ("planned", "published", "cancelled")


class ScheduledPost(db.Model):
    __tablename__ = "scheduled_posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id = db.Column(
        db.Integer,
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ai_generation_id = db.Column(
        db.Integer,
        db.ForeignKey("ai_generations.id", ondelete="SET NULL"),
        nullable=True,
    )
    social_account_id = db.Column(
        db.Integer,
        db.ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    caption = db.Column(db.Text, nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="planned", nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    workspace = db.relationship("Workspace", back_populates="scheduled_posts")
    ai_generation = db.relationship("AIGeneration", back_populates="scheduled_post")
    social_account = db.relationship("SocialAccount")

    def __repr__(self) -> str:
        return f"<ScheduledPost {self.id} {self.status}>"

    def to_dict(self) -> dict:
        account = self.social_account
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "ai_generation_id": self.ai_generation_id,
            "social_account_id": self.social_account_id,
            "caption": self.caption,
            "scheduled_at": iso(self.scheduled_at),
            "status": self.status,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
            "platform": account.platform if account else None,
            "handle": account.handle if account else None,
        }
