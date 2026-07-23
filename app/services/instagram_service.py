"""Instagram integration via the Instagram Graph API (OAuth, "Instagram Login").

Real follower/media metrics for the **authenticated user's own Business or
Creator account**. Unlike YouTube, Instagram offers *no* public, key-based
lookup for an arbitrary ``@handle`` — Meta deprecated the Basic Display API in
December 2024 and requires OAuth for all metrics — so there is deliberately no
"track any public account" mode here.

Flow (mirrors ``youtube_service``):

1. :func:`get_authorization_url` — send the user to Meta's consent screen.
2. :func:`exchange_code` — swap the returned code for a long-lived token.
3. :func:`fetch_profile_stats` — read ``followers_count``/``media_count``.

When ``INSTAGRAM_APP_ID``/``INSTAGRAM_APP_SECRET`` are unset,
:func:`is_configured` returns ``False`` and callers fall back to Demo Mode so
the product stays usable locally. ``requests`` is imported lazily so the API
boots even if it is unavailable.
"""

import secrets
from urllib.parse import urlencode

from flask import current_app

# Instagram Login endpoints (graph.instagram.com — no Facebook Page required).
_AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
_GRAPH_BASE = "https://graph.instagram.com"
# Minimal scope needed to read profile + follower/media counts.
_SCOPES = "instagram_business_basic"
_PROFILE_FIELDS = "id,username,account_type,followers_count,media_count"
_TIMEOUT = 15


def is_configured() -> bool:
    """True when a Meta app is configured for the OAuth connect flow."""
    return bool(
        current_app.config.get("INSTAGRAM_APP_ID")
        and current_app.config.get("INSTAGRAM_APP_SECRET")
    )


def get_authorization_url() -> tuple[str, str]:
    """Return ``(authorization_url, state)`` for Meta's consent screen."""
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": current_app.config["INSTAGRAM_APP_ID"],
        "redirect_uri": current_app.config["INSTAGRAM_REDIRECT_URI"],
        "scope": _SCOPES,
        "response_type": "code",
        "state": state,
    }
    return f"{_AUTHORIZE_URL}?{urlencode(params)}", state


def exchange_code(code: str) -> dict:
    """Exchange an auth code for a long-lived access token + Instagram user id.

    Meta returns a short-lived token first; we immediately upgrade it to the
    60-day long-lived token so daily snapshots keep working.
    """
    import requests

    short = requests.post(
        _TOKEN_URL,
        data={
            "client_id": current_app.config["INSTAGRAM_APP_ID"],
            "client_secret": current_app.config["INSTAGRAM_APP_SECRET"],
            "grant_type": "authorization_code",
            "redirect_uri": current_app.config["INSTAGRAM_REDIRECT_URI"],
            "code": code,
        },
        timeout=_TIMEOUT,
    )
    short.raise_for_status()
    payload = short.json()
    access_token = payload.get("access_token")
    user_id = str(payload.get("user_id") or "")
    if not access_token:
        raise RuntimeError("Instagram did not return an access token.")

    long = requests.get(
        f"{_GRAPH_BASE}/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": current_app.config["INSTAGRAM_APP_SECRET"],
            "access_token": access_token,
        },
        timeout=_TIMEOUT,
    )
    if long.ok:
        access_token = long.json().get("access_token", access_token)
    return {"access_token": access_token, "user_id": user_id}


def fetch_profile_stats(access_token: str, user_id: str | None = None) -> dict:
    """Return ``{external_id, username, account_type, follower_count, media_count}``.

    Reads the authenticated professional account's profile. ``user_id`` is
    optional — the ``/me`` alias resolves from the token when it is absent.
    """
    import requests

    target = user_id or "me"
    resp = requests.get(
        f"{_GRAPH_BASE}/{target}",
        params={"fields": _PROFILE_FIELDS, "access_token": access_token},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "external_id": str(data.get("id") or user_id or ""),
        "username": data.get("username") or "Instagram Account",
        "account_type": data.get("account_type"),
        "follower_count": int(data.get("followers_count", 0) or 0),
        "media_count": int(data.get("media_count", 0) or 0),
    }
