"""Canonical enum/role constants shared across the app.

Kept in one place so models, middleware and controllers agree on allowed values.
"""

# Workspace membership roles.
ROLE_OWNER = "owner"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"
ALL_ROLES = (ROLE_OWNER, ROLE_EDITOR, ROLE_VIEWER)
EDITOR_ROLES = (ROLE_OWNER, ROLE_EDITOR)
OWNER_ONLY = (ROLE_OWNER,)
PLATFORM_ADMIN = "platform_admin"

# Plan tiers.
PLAN_TIERS = ("free", "pro", "agency")

# Social platforms.
PLATFORMS = ("youtube", "instagram", "tiktok", "twitter")
DEMO_PLATFORMS = ("instagram", "tiktok", "twitter")

# AI generation types.
GENERATION_TYPES = ("caption", "hashtags", "content_idea", "viral_score", "sentiment")

# Grade scale (best -> worst).
GRADE_SCALE = ("A++", "A+", "A", "B+", "B", "C", "D", "F")
