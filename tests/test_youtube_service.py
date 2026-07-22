from app.services import youtube_service


def test_not_configured_without_keys(app):
    with app.app_context():
        assert youtube_service.is_configured() is False


def test_scopes_are_readonly():
    assert youtube_service._SCOPES == [
        "https://www.googleapis.com/auth/youtube.readonly"
    ]
