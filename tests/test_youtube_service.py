import pytest

from app.services import youtube_service

_CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw"


def test_not_configured_without_keys(app):
    with app.app_context():
        assert youtube_service.is_configured() is False


def test_public_not_configured_without_api_key(app):
    with app.app_context():
        assert youtube_service.is_public_configured() is False


def test_scopes_are_readonly():
    assert youtube_service._SCOPES == [
        "https://www.googleapis.com/auth/youtube.readonly"
    ]


@pytest.mark.parametrize(
    "raw,expected",
    [
        (f"https://www.youtube.com/channel/{_CHANNEL_ID}", {"kind": "channel_id", "value": _CHANNEL_ID}),
        (_CHANNEL_ID, {"kind": "channel_id", "value": _CHANNEL_ID}),
        ("https://youtube.com/@mkbhd", {"kind": "handle", "value": "@mkbhd"}),
        ("@mkbhd", {"kind": "handle", "value": "@mkbhd"}),
        ("mkbhd", {"kind": "handle", "value": "@mkbhd"}),
        ("https://www.youtube.com/user/LinusTechTips", {"kind": "username", "value": "LinusTechTips"}),
        ("https://www.youtube.com/c/LinusTechTips", {"kind": "search", "value": "LinusTechTips"}),
        ("youtube.com/@mkbhd", {"kind": "handle", "value": "@mkbhd"}),
    ],
)
def test_parse_channel_input(raw, expected):
    assert youtube_service.parse_channel_input(raw) == expected


def test_parse_channel_input_rejects_empty():
    with pytest.raises(ValueError):
        youtube_service.parse_channel_input("   ")
