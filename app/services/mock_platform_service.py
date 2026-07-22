"""Demo/mock platform data generator.

Produces a deterministic-but-plausible growth curve seeded from the social
account id, so demo data is stable and reproducible across snapshot runs.
Every value derived here backs a **Demo Mode** account and must be labelled as
such in responses and UI.
"""

import hashlib
import random
from datetime import date

# Anchor for the growth curve; days elapsed since this date drive compounding.
_GROWTH_ANCHOR = date(2026, 1, 1)


def _account_seed(social_account) -> int:
    raw = f"{social_account.id}:{social_account.platform}:{social_account.handle}"
    return int(hashlib.sha256(raw.encode()).hexdigest(), 16)


def point_for_date(social_account, target_date: date) -> dict:
    """Deterministic ``{follower_count, view_count, engagement_rate}`` for a day."""
    seed = _account_seed(social_account)
    base_followers = 800 + (seed % 12000)
    daily_rate = 0.002 + (seed % 60) / 10000.0  # ~0.2%–0.8% per day

    elapsed = max((target_date - _GROWTH_ANCHOR).days, 0)
    followers = base_followers * ((1 + daily_rate) ** elapsed)

    # Small deterministic per-day jitter so the curve isn't perfectly smooth.
    jitter = random.Random(seed ^ target_date.toordinal())
    followers *= 1 + jitter.uniform(-0.002, 0.004)
    followers = int(followers)

    views_multiplier = 40 + (seed % 120)
    view_count = int(followers * views_multiplier)

    engagement = 2.0 + (seed % 500) / 100.0 + jitter.uniform(-0.4, 0.6)
    engagement = round(max(0.5, min(engagement, 12.0)), 2)

    return {
        "follower_count": max(followers, 0),
        "view_count": max(view_count, 0),
        "engagement_rate": engagement,
    }


def generate_daily_point(social_account) -> dict:
    """Today's plausible data point for a demo account."""
    return point_for_date(social_account, date.today())
