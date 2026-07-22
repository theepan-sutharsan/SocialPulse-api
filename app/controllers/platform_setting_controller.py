"""Platform-wide settings & feature flags.

Feature flags are global booleans owned by platform admins that toggle optional
product behaviour for *every* user. Values are persisted in ``platform_settings``
and fall back to :data:`FEATURE_FLAGS` defaults when a row has not been written
yet, so the app works out of the box before an admin touches anything.
"""

from flask import jsonify, request

from app.extensions import db
from app.models.platform_setting_model import PlatformSetting

# Public boolean feature flags with their default (out-of-the-box) state.
FEATURE_FLAGS: dict[str, bool] = {
    # When enabled, users can press the "d" key to toggle light/dark theme.
    "keyboard_theme_toggle": True,
}

_TRUTHY = {"1", "true", "yes", "on"}


def _to_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in _TRUTHY


def get_flag(key: str) -> bool:
    """Resolve a feature flag, honouring the stored value or its default."""
    default = FEATURE_FLAGS.get(key, False)
    setting = PlatformSetting.query.filter_by(key=key).first()
    if setting is None:
        return default
    return _to_bool(setting.value, default)


def set_flag(key: str, value: bool) -> None:
    """Upsert a feature flag value (caller commits)."""
    stored = "true" if value else "false"
    setting = PlatformSetting.query.filter_by(key=key).first()
    if setting is None:
        db.session.add(PlatformSetting(key=key, value=stored))
    else:
        setting.value = stored


def current_flags() -> dict[str, bool]:
    return {key: get_flag(key) for key in FEATURE_FLAGS}


def public_feature_flags():
    """Public: feature flags the frontend needs to configure its UI."""
    return jsonify({"feature_flags": current_flags()}), 200


def admin_list_settings():
    """Admin: current feature-flag values (defaults applied for unset keys)."""
    return jsonify({"feature_flags": current_flags()}), 200


def admin_update_settings():
    """Admin: update one or more boolean feature flags.

    Accepts either ``{"feature_flags": {...}}`` or a bare ``{...}`` map of
    ``flag -> bool``. Unknown flags are rejected to avoid silent typos.
    """
    data = request.get_json(silent=True) or {}
    updates = data.get("feature_flags", data)
    if not isinstance(updates, dict) or not updates:
        return jsonify({"errors": ["feature_flags must be a non-empty object."]}), 400

    unknown = [key for key in updates if key not in FEATURE_FLAGS]
    if unknown:
        return (
            jsonify({"errors": [f"Unknown feature flag(s): {', '.join(unknown)}."]}),
            400,
        )

    for key, value in updates.items():
        set_flag(key, _to_bool(value))

    try:
        db.session.commit()
    except Exception:  # noqa: BLE001 - surface a clean 500 to the client
        db.session.rollback()
        return jsonify({"error": "Could not update settings."}), 500

    return (
        jsonify({"message": "Settings updated.", "feature_flags": current_flags()}),
        200,
    )
