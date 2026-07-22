"""Celery application bound to the Flask app context.

Run the worker + beat with:

    celery -A worker.celery_app.celery worker --loglevel=info
    celery -A worker.celery_app.celery beat --loglevel=info
"""

from celery.schedules import crontab

from app import create_app
from app.extensions import celery

flask_app = create_app()
celery.conf.update(
    broker_url=flask_app.config["REDIS_URL"],
    result_backend=flask_app.config["REDIS_URL"],
    timezone="UTC",
)


class ContextTask(celery.Task):
    """Ensure every task runs inside the Flask application context."""

    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask

# Beat schedule: daily snapshot job (and weekly digest stretch goal).
celery.conf.beat_schedule = {
    "run-daily-snapshots": {
        "task": "worker.tasks.run_daily_snapshots",
        "schedule": crontab(hour=2, minute=0),
    },
    "send-weekly-digest": {
        "task": "worker.tasks.send_weekly_digest",
        "schedule": crontab(day_of_week="mon", hour=8, minute=0),
    },
}

# Import tasks so they register with the app.
from worker import tasks  # noqa: E402,F401
