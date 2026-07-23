"""YouTube Data API v3 integration.

Two modes are supported:

* **OAuth 2.0** (``is_configured``) — the channel owner authorizes access; used
  by the *Connect* flow. Tokens are stored encrypted at rest by the caller.
* **API key** (``is_public_configured``) — SocialBlade-style *tracking* of any
  public channel by URL/handle, with no login. Used by the *Track* flow and by
  daily snapshots to refresh real public stats.

All Google client libraries are imported lazily so the API boots without them
installed.
"""

import re
from urllib.parse import urlparse

from flask import current_app

_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# A YouTube channel id is "UC" followed by 22 url-safe base64 chars.
_CHANNEL_ID_RE = re.compile(r"^UC[0-9A-Za-z_-]{22}$")
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def is_configured() -> bool:
    return bool(
        current_app.config.get("YOUTUBE_CLIENT_ID")
        and current_app.config.get("YOUTUBE_CLIENT_SECRET")
    )


def is_public_configured() -> bool:
    """True when an API key is available for public (no-OAuth) tracking."""
    return bool(current_app.config.get("YOUTUBE_API_KEY"))


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


# --- Public (API-key) tracking ----------------------------------------------------


def parse_channel_input(raw: str) -> dict:
    """Parse a channel URL/handle into a lookup descriptor.

    Returns ``{"kind": ..., "value": ...}`` where ``kind`` is one of
    ``channel_id``, ``handle``, ``username`` or ``search``. Pure function (no
    network) so it is cheap to unit-test. Raises ``ValueError`` on empty input.
    """
    text = (raw or "").strip()
    if not text:
        raise ValueError("A channel URL or handle is required.")

    if text.startswith("@"):
        return {"kind": "handle", "value": text}
    if _CHANNEL_ID_RE.match(text):
        return {"kind": "channel_id", "value": text}

    if "youtube.com" in text or "youtu.be" in text:
        url = text if "://" in text else f"https://{text}"
        segments = [s for s in urlparse(url).path.split("/") if s]
        if not segments:
            raise ValueError("Could not find a channel in that YouTube URL.")
        first = segments[0]
        if first.startswith("@"):
            return {"kind": "handle", "value": first}
        if first == "channel" and len(segments) > 1:
            return {"kind": "channel_id", "value": segments[1]}
        if first == "user" and len(segments) > 1:
            return {"kind": "username", "value": segments[1]}
        if first == "c" and len(segments) > 1:
            return {"kind": "search", "value": segments[1]}
        return {"kind": "search", "value": first}

    # Bare token: treat a safe word as a handle, anything else as a search.
    if _SAFE_NAME_RE.match(text):
        return {"kind": "handle", "value": f"@{text}"}
    return {"kind": "search", "value": text}


def _public_client():
    from googleapiclient.discovery import build

    return build(
        "youtube",
        "v3",
        developerKey=current_app.config["YOUTUBE_API_KEY"],
        cache_discovery=False,
    )


def _channel_by(resource, **kwargs):
    response = (
        resource.channels().list(part="snippet,statistics", **kwargs).execute()
    )
    items = response.get("items", [])
    return items[0] if items else None


def _search_channel(resource, query: str):
    response = (
        resource.search()
        .list(part="snippet", type="channel", q=query, maxResults=1)
        .execute()
    )
    items = response.get("items", [])
    if not items:
        return None
    channel_id = items[0].get("id", {}).get("channelId") or items[0].get(
        "snippet", {}
    ).get("channelId")
    return _channel_by(resource, id=channel_id) if channel_id else None


def _resolve_channel(resource, parsed: dict):
    kind, value = parsed["kind"], parsed["value"]
    if kind == "channel_id":
        return _channel_by(resource, id=value)
    if kind == "handle":
        return _channel_by(resource, forHandle=value) or _search_channel(
            resource, value.lstrip("@")
        )
    if kind == "username":
        return _channel_by(resource, forUsername=value) or _search_channel(
            resource, value
        )
    return _search_channel(resource, value)


def _normalize_channel(channel: dict | None, fallback: str) -> dict:
    if not channel:
        raise LookupError("No YouTube channel found for that URL or handle.")
    stats = channel.get("statistics", {})
    snippet = channel.get("snippet", {})
    return {
        "channel_id": channel.get("id"),
        "handle": snippet.get("title") or fallback or "YouTube Channel",
        "custom_url": snippet.get("customUrl"),
        "subscriber_count": int(stats.get("subscriberCount", 0) or 0),
        "view_count": int(stats.get("viewCount", 0) or 0),
        "hidden_subscriber_count": bool(stats.get("hiddenSubscriberCount", False)),
    }


def fetch_public_channel_stats(url_or_handle: str) -> dict:
    """Resolve a public channel from a URL/handle and return normalized stats.

    Raises ``ValueError`` for unparseable input and ``LookupError`` when no
    channel matches.
    """
    parsed = parse_channel_input(url_or_handle)
    channel = _resolve_channel(_public_client(), parsed)
    return _normalize_channel(channel, parsed["value"])


def fetch_public_stats_by_channel_id(channel_id: str) -> dict:
    """Fetch normalized public stats for a known channel id (daily snapshots)."""
    channel = _channel_by(_public_client(), id=channel_id)
    return _normalize_channel(channel, channel_id)
