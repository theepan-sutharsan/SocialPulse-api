"""Pytest fixtures. Uses a temporary SQLite database so tests need no MySQL."""

import os
import tempfile

_db_fd, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-plenty-long-1234567890"
os.environ["AI_PRIMARY_PROVIDER"] = "anthropic"  # no keys -> local fallback

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402


@pytest.fixture()
def app():
    application = create_app()
    application.config.update(TESTING=True)
    with application.app_context():
        _db.drop_all()
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth(client):
    """Register a fresh owner and return ready-to-use auth headers + context."""
    from tests.helpers import register

    return register(client)
