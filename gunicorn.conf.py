"""Gunicorn production config tuned for small container deployments."""

import os

# Railway plans typically have limited memory. One gthread worker is enough for
# this synchronous Flask API and avoids multiplying the application's memory
# footprint by the container CPU count.
bind = os.getenv("GUNICORN_BIND", f"0.0.0.0:{os.getenv('PORT', '5000')}")
workers = int(os.getenv("GUNICORN_WORKERS", "1"))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")