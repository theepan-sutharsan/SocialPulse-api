"""Workspace model — the multi-tenant boundary.

Every tenant-owned record carries a ``workspace_id``. Media-kit branding fields
(bio, tagline, brand colour, logo, white-label flag) live here since the
media-kit page is rendered from workspace + social-account data.
"""

from app.extensions import db
from app.utils import iso, utc_now

PLAN_TIERS = ("free", "pro", "agency")


class Workspace(db.Model):
    __tablename__ = "workspaces"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    plan_tier = db.Column(db.String(20), default="free", nullable=False)
    is_agency = db.Column(db.Boolean, default=False, nullable=False)

    # Media-kit / white-label branding.
    bio = db.Column(db.Text, nullable=True)
    tagline = db.Column(db.String(255), nullable=True)
    brand_color = db.Column(db.String(9), nullable=True)
    logo_url = db.Column(db.String(512), nullable=True)
    is_white_label = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    members = db.relationship(
        "WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan"
    )
    social_accounts = db.relationship(
        "SocialAccount", back_populates="workspace", cascade="all, delete-orphan"
    )
    ai_generations = db.relationship(
        "AIGeneration", back_populates="workspace", cascade="all, delete-orphan"
    )
    scheduled_posts = db.relationship(
        "ScheduledPost", back_populates="workspace", cascade="all, delete-orphan"
    )
    subscription = db.relationship(
        "Subscription",
        back_populates="workspace",
        uselist=False,
        cascade="all, delete-orphan",
    )
    credit_usages = db.relationship(
        "CreditUsage", back_populates="workspace", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Workspace {self.id} {self.slug}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "plan_tier": self.plan_tier,
            "is_agency": self.is_agency,
            "bio": self.bio,
            "tagline": self.tagline,
            "brand_color": self.brand_color,
            "logo_url": self.logo_url,
            "is_white_label": self.is_white_label,
            "member_count": len(self.members),
            "created_at": iso(self.created_at),
        }
