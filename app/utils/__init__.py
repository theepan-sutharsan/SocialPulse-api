"""Shared helper utilities used across models, controllers and services."""

import re
from datetime import date, datetime, timezone


def utc_now() -> datetime:
    """Timezone-aware current UTC timestamp (used as column default)."""
    return datetime.now(timezone.utc)


def slugify(value: str) -> str:
    """Lowercase, hyphenated, URL-safe slug from arbitrary text."""
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "workspace"


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str) -> bool:
    return bool(value and EMAIL_RE.match(value.strip()))


def iso(value) -> str | None:
    """Serialize a date/datetime to ISO-8601, tolerating ``None``."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def parse_date(value) -> date | None:
    """Parse an ISO date string (``YYYY-MM-DD``) into a ``date``."""
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def parse_datetime(value) -> datetime | None:
    """Parse an ISO-8601 datetime string into a timezone-aware datetime."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


__all__ = [
    "utc_now",
    "iso",
    "parse_date",
    "parse_datetime",
    "slugify",
    "is_valid_email",
]
