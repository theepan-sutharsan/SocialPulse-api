"""Shared extension singletons.

These are instantiated here (without an app) and bound to the application
inside :func:`app.create_app` to avoid circular imports.
"""

from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()

# Celery is optional for the API process (only the worker strictly needs it), so
# the import is guarded — the API boots fine without the background stack.
try:
    from celery import Celery

    celery = Celery(__name__)
except Exception:  # pragma: no cover - celery not installed
    celery = None
