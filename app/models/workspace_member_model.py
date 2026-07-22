"""WorkspaceMember — the many-to-many junction between users and workspaces.

SIGNATURE relationship: one row per user per workspace, each with its own role.
Unique on ``(user_id, workspace_id)``.
"""

from app.extensions import db
from app.utils import iso, utc_now

ROLES = ("owner", "editor", "viewer")


class WorkspaceMember(db.Model):
    __tablename__ = "workspace_members"
    __table_args__ = (
        db.UniqueConstraint("user_id", "workspace_id", name="uq_member_user_workspace"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id = db.Column(
        db.Integer, db.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    role = db.Column(db.String(20), default="editor", nullable=False)
    invited_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    joined_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    user = db.relationship("User", back_populates="memberships")
    workspace = db.relationship("Workspace", back_populates="members")

    def __repr__(self) -> str:
        return f"<WorkspaceMember u{self.user_id} w{self.workspace_id} {self.role}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "role": self.role,
            "invited_at": iso(self.invited_at),
            "joined_at": iso(self.joined_at),
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
            # Convenience denormalization for member tables in the UI.
            "user_email": self.user.email if self.user else None,
            "user_full_name": self.user.full_name if self.user else None,
        }
