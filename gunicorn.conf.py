"""Gunicorn production config.

Memory-optimized for constrained environments (e.g. Railway Hobby plan,
1GB memory limit per replica). Each worker loads Flask plus the full set
of AI SDK dependencies (Anthropic, OpenAI, Google, NVIDIA, OpenRouter),
which can consume ~400-500MB per worker. Spawning workers based on
cpu_count() * 2 + 1 (often 5+) exhausts available memory and causes
SIGKILL/OOM kills. We hardcode a conservative worker/thread count instead.
"""

import os

port = os.getenv("PORT", "5000")
bind = os.getenv("GUNICORN_BIND", f"0.0.0.0:{port}")
# 2 workers keeps memory usage predictable (~500MB/worker on a 1GB limit).
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "sync"
# 1 thread per worker to avoid additional per-worker memory overhead.
threads = int(os.getenv("GUNICORN_THREADS", "1"))
# Long timeout to accommodate long-running AI generation requests.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
# Allow workers time to finish in-flight requests during graceful restarts.
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
