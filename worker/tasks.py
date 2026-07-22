"""Celery tasks: the daily snapshot job and (stretch) the weekly email digest."""

import logging

from app.extensions import celery
from app.services import snapshot_service

logger = logging.getLogger(__name__)


@celery.task(name="worker.tasks.run_daily_snapshots")
def run_daily_snapshots():
    """Insert one AnalyticsSnapshot per connected account (idempotent per day)."""
    result = snapshot_service.run_daily_snapshots()
    logger.info("run_daily_snapshots: %s", result)
    return result


@celery.task(name="worker.tasks.send_weekly_digest")
def send_weekly_digest():
    """Stretch goal: weekly growth email digest. No-op placeholder for v1."""
    logger.info("send_weekly_digest invoked (not implemented in v1).")
    return {"sent": 0}
