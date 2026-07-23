"""Unit tests for the Instagram Graph API service (no network required)."""

from urllib.parse import parse_qs, urlparse

from app.services import instagram_service


def test_not_configured_without_keys(app):
    with app.app_context():
        assert instagram_service.is_configured() is False


def test_configured_with_keys(app):
    with app.app_context():
        app.config["INSTAGRAM_APP_ID"] = "app-123"
        app.config["INSTAGRAM_APP_SECRET"] = "secret-xyz"
        assert instagram_service.is_configured() is True


def test_scope_is_business_basic():
    # Real metrics need a professional account; basic profile scope is enough.
    assert instagram_service._SCOPES == "instagram_business_basic"


def test_authorization_url_contains_client_and_scope(app):
    with app.app_context():
        app.config["INSTAGRAM_APP_ID"] = "app-123"
        app.config["INSTAGRAM_APP_SECRET"] = "secret-xyz"
        app.config["INSTAGRAM_REDIRECT_URI"] = "https://example.test/cb"
        url, state = instagram_service.get_authorization_url()

    assert url.startswith("https://www.instagram.com/oauth/authorize")
    query = parse_qs(urlparse(url).query)
    assert query["client_id"] == ["app-123"]
    assert query["redirect_uri"] == ["https://example.test/cb"]
    assert query["scope"] == ["instagram_business_basic"]
    assert query["response_type"] == ["code"]
    assert query["state"] == [state]
    assert state  # a non-empty CSRF token is generated
