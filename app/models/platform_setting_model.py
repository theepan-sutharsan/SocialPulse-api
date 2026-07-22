"""PlatformSetting — global key/value store for platform-wide feature flags.

A single row per feature flag, managed by platform admins and read by every
client (including logged-out visitors) to decide which optional UI behaviours —
such as the keyboard theme-toggle shortcut — are enabled for all users.
"""

from app.extensions import db
from app.utils import iso, utc_now


class PlatformSetting(db.Model):
    __tablename__ = "platform_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    value = db.Column(db.String(255), nullable=False, default="")
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    def __repr__(self) -> str:
        return f"<PlatformSetting {self.key}={self.value!r}>"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": iso(self.updated_at),
        }
