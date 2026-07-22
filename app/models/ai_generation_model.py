"""AIGeneration — a single AI generation call and its (editable) result."""

from app.extensions import db
from app.utils import iso, utc_now

GENERATION_TYPES = ("caption", "hashtags", "content_idea", "viral_score", "sentiment")


class AIGeneration(db.Model):
    __tablename__ = "ai_generations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id = db.Column(
        db.Integer, db.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    social_account_id = db.Column(
        db.Integer,
        db.ForeignKey("social_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    generation_type = db.Column(db.String(30), nullable=False)
    prompt_input = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text, nullable=True)
    provider = db.Column(db.String(50), nullable=True)
    credits_used = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    workspace = db.relationship("Workspace", back_populates="ai_generations")
    social_account = db.relationship("SocialAccount")
    scheduled_post = db.relationship(
        "ScheduledPost", back_populates="ai_generation", uselist=False
    )

    def __repr__(self) -> str:
        return f"<AIGeneration {self.id} {self.generation_type}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "social_account_id": self.social_account_id,
            "generation_type": self.generation_type,
            "prompt_input": self.prompt_input,
            "result": self.result,
            "provider": self.provider,
            "credits_used": self.credits_used,
            "created_at": iso(self.created_at),
        }
