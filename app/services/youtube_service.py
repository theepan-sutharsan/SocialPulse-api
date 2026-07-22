"""YouTube Data API v3 live integration (OAuth 2.0).

All Google client libraries are imported lazily so the API boots without them
installed. When ``YOUTUBE_CLIENT_ID``/``SECRET`` are unset, :func:`is_configured`
returns False and callers fall back to seeded live-shaped data (see spec §19).
Tokens are stored encrypted at rest by the caller.
"""

from flask import current_app

_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


def is_configured() -> bool:
    return bool(
        current_app.config.get("YOUTUBE_CLIENT_ID")
        and current_app.config.get("YOUTUBE_CLIENT_SECRET")
    )


def _client_config() -> dict:
    return {
        "web": {
            "client_id": current_app.config["YOUTUBE_CLIENT_ID"],
            "client_secret": current_app.config["YOUTUBE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [current_app.config["YOUTUBE_REDIRECT_URI"]],
        }
    }


def get_authorization_url() -> tuple[str, str]:
    """Return ``(authorization_url, state)`` for the consent screen."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(_client_config(), scopes=_SCOPES)
    flow.redirect_uri = current_app.config["YOUTUBE_REDIRECT_URI"]
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    return auth_url, state


def exchange_code(code: str) -> dict:
    """Exchange an authorization code for access + refresh tokens."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(_client_config(), scopes=_SCOPES)
    flow.redirect_uri = current_app.config["YOUTUBE_REDIRECT_URI"]
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {"access_token": creds.token, "refresh_token": creds.refresh_token}


def fetch_channel_stats(access_token: str) -> dict:
    """Fetch ``{subscriber_count, view_count, handle}`` via channels.list."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(token=access_token)
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    response = (
        youtube.channels()
        .list(part="snippet,statistics", mine=True)
        .execute()
    )
    items = response.get("items", [])
    if not items:
        raise RuntimeError("No YouTube channel found for this account.")
    channel = items[0]
    stats = channel.get("statistics", {})
    snippet = channel.get("snippet", {})
    return {
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "view_count": int(stats.get("viewCount", 0)),
        "handle": snippet.get("title", "YouTube Channel"),
    }
