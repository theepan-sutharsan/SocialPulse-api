"""Pytest fixtures. Uses a temporary SQLite database so tests need no MySQL."""

import os
import tempfile

_db_fd, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-plenty-long-1234567890"
os.environ["AI_PRIMARY_PROVIDER"] = "anthropic"  # no keys -> local fallback

# Keep the suite hermetic: blank out real integration credentials so tests do
# not depend on whatever is in the developer's local `.env`. Set (not pop) to ""
# so python-dotenv's non-overriding load won't repopulate them from `.env`.
# AI keys are blanked so generation tests exercise the deterministic local
# fallback (as documented above) rather than calling real providers.
for _var in (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "NVIDIA_API_KEY",
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_API_KEY",
    "INSTAGRAM_APP_ID",
    "INSTAGRAM_APP_SECRET",
):
    os.environ[_var] = ""

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402


@pytest.fixture()
def app():
    application = create_app()
    application.config.update(TESTING=True)
    with application.app_context():
        from app.services import ai_service

        ai_service._CACHE.clear()
        _db.drop_all()
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()
        ai_service._CACHE.clear()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth(client):
    """Register a fresh owner and return ready-to-use auth headers + context."""
    from tests.helpers import register

    return register(client)
