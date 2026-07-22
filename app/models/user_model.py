"""User account model with hashed-password auth helpers."""

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils import iso, utc_now


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    is_platform_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    memberships = db.relationship(
        "WorkspaceMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, raw_password: str) -> None:
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password, raw_password)

    def workspaces_payload(self) -> list[dict]:
        """Workspace list (with the caller's role) for the workspace switcher."""
        return [
            {**m.workspace.to_dict(), "role": m.role, "member_id": m.id}
            for m in self.memberships
        ]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_platform_admin": self.is_platform_admin,
            "is_active": self.is_active,
            "created_at": iso(self.created_at),
        }
