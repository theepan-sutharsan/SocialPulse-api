from app.config import Config


def test_request_body_cap(app):
    assert app.config["MAX_CONTENT_LENGTH"] == 5 * 1024 * 1024


def test_json_keys_not_sorted(app):
    assert app.config["JSON_SORT_KEYS"] is False


def test_plan_credits_increase_with_tier():
    assert Config.PLAN_CREDITS["free"] >= 1
    assert Config.PLAN_CREDITS["pro"] > Config.PLAN_CREDITS["free"]
    assert Config.PLAN_CREDITS["agency"] > Config.PLAN_CREDITS["pro"]
