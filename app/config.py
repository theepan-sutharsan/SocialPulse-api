"""Central configuration loaded from environment variables.

All secrets and connection strings are read from the environment (via
``python-dotenv``) so nothing sensitive is hard-coded. A single ``Config``
class is consumed by the application factory.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration — reads every setting from the environment."""

    # --- Core ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    FLASK_DEBUG = _bool(os.getenv("FLASK_DEBUG"), True)
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # Response behaviour
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # cap request bodies at 5 MB

    # --- Database (MySQL via PyMySQL) ---
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "social_ai_saas")

    _DEFAULT_DB_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _DEFAULT_DB_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # --- Auth (JWT) ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "1440"))
    )

    # --- Encryption of OAuth tokens at rest (derived from JWT secret if unset) ---
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

    # --- AI providers ---
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # OpenAI Responses API model used for text generation.
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    # Gemini (Google AI Studio) — REST generateContent. Prefer this over the
    # google-generativeai SDK which breaks on newer Python/protobuf combos.
    GEMINI_BASE_URL = os.getenv(
        "GEMINI_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta",
    )
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    # NVIDIA NIM (OpenAI-compatible) — e.g. DiffusionGemma on build.nvidia.com
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    NVIDIA_BASE_URL = os.getenv(
        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
    )
    NVIDIA_MODEL = os.getenv(
        "NVIDIA_MODEL", "google/diffusiongemma-26b-a4b-it"
    )
    # OpenRouter unified model API (OpenAI-compatible).
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/auto-beta")
    OPENROUTER_SITE_URL = os.getenv(
        "OPENROUTER_SITE_URL", "http://localhost:3000"
    )
    OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Social Pulse")
    AI_PRIMARY_PROVIDER = os.getenv("AI_PRIMARY_PROVIDER", "anthropic")
    AI_CACHE_TTL_SECONDS = int(os.getenv("AI_CACHE_TTL_SECONDS", "300"))

    # --- YouTube Data API v3 ---
    YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
    YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
    YOUTUBE_REDIRECT_URI = os.getenv(
        "YOUTUBE_REDIRECT_URI",
        "http://127.0.0.1:5000/api/social-accounts/connect/youtube/callback",
    )
    # API key for public (no-OAuth) channel tracking, SocialBlade-style.
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    # --- Instagram Graph API (OAuth; Business/Creator accounts only) ---
    # Instagram has no public metrics endpoint, so real data requires OAuth via
    # a Meta app. Unset => Instagram falls back to Demo Mode.
    INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID")
    INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
    INSTAGRAM_REDIRECT_URI = os.getenv(
        "INSTAGRAM_REDIRECT_URI",
        "http://127.0.0.1:5000/api/social-accounts/connect/instagram/callback",
    )

    # --- Billing ---
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

    # --- Infra ---
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SENTRY_DSN = os.getenv("SENTRY_DSN")

    # --- Frontend origin (billing redirect URLs) ---
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # --- Plan catalog: monthly AI credit allotment per tier ---
    PLAN_CREDITS = {"free": 5, "pro": 500, "agency": 5000}
    PLAN_PRICES_USD = {"free": 0, "pro": 29, "agency": 99}
    PLAN_PRICES_INR = {"free": 0, "pro": 2400, "agency": 8000}
