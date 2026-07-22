from app import constants


def test_role_sets():
    assert constants.ROLE_OWNER in constants.ALL_ROLES
    assert set(constants.EDITOR_ROLES) == {"owner", "editor"}
    assert constants.OWNER_ONLY == ("owner",)


def test_plan_tiers_and_platforms():
    assert constants.PLAN_TIERS == ("free", "pro", "agency")
    assert "youtube" in constants.PLATFORMS
    assert "youtube" not in constants.DEMO_PLATFORMS


def test_generation_types():
    assert set(constants.GENERATION_TYPES) == {
        "caption",
        "hashtags",
        "content_idea",
        "viral_score",
        "sentiment",
    }
