"""Public platform-settings blueprint — /api/settings.

Exposes the read-only feature-flag map that the frontend fetches on boot to
decide which optional behaviours (e.g. the keyboard theme shortcut) to enable.
No authentication required: the flags apply to every visitor, signed in or not.
"""

from flask import Blueprint

from app.controllers import platform_setting_controller as ctrl

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@settings_bp.get("/public")
def public_settings():
    return ctrl.public_feature_flags()
