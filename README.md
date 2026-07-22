# AI Social Media Analytics & Content SaaS — API

Flask REST API for a multi-tenant, AI-powered social media analytics & content
platform. Creators connect social accounts, a daily job records SocialBlade-style
growth snapshots, and an AI layer generates captions/hashtags/ideas/viral-score/
sentiment — gated behind freemium billing.

> Backend for the spec in `../Social-Media-AI-SaaS-Project-Structure.md`.
> **Database:** MySQL (SQLAlchemy + PyMySQL).

## Tech stack

- Python 3.12+ · Flask 3 (application factory) · SQLAlchemy 2 / Flask-SQLAlchemy
- MySQL via PyMySQL · Flask-JWT-Extended (Bearer auth) · Flask-CORS
- Anthropic / OpenAI / Gemini (multi-provider AI with fallback + caching)
- YouTube Data API v3 (live OAuth) · Stripe + Razorpay (billing)
- Celery + Redis (daily snapshot job) · reportlab (PDF) · stdlib csv (CSV)

## Architecture

```
run.py                 # entrypoint -> create_app()
app/
  __init__.py          # factory: extensions, JWT, error handlers, blueprints
  config.py            # env-driven configuration
  extensions.py        # db, jwt, (optional) celery singletons
  middleware.py        # roles_required / workspace_scoped / login_required
  models/              # SQLAlchemy models (one per entity)
  controllers/         # business logic (thin routes delegate here)
  routes/              # blueprints, url_prefix="/api/..."
  services/            # ai / youtube / mock_platform / billing / snapshot
  utils/               # csv_utils, pdf_utils, security, helpers
worker/                # celery app + tasks (daily snapshots, weekly digest)
seed.py                # demo data (run: python seed.py)
tests/                 # pytest suite (SQLite-backed)
```

Key design points:

- **Multi-tenant isolation** — every tenant-owned query filters by
  `current_workspace.id`; the workspace is resolved from the `X-Workspace-Id`
  header and validated against `workspace_members`.
- **Signature many-to-many** — `workspace_members` links users ↔ workspaces with
  a per-membership role (`owner`/`editor`/`viewer`).
- **Signature time-series** — `analytics_snapshots` stores one row per account
  per day (unique on `social_account_id + snapshot_date`).
- **AI credit metering** — `/api/generate/*` checks the monthly ledger before any
  provider call; credits are deducted only on a successful, non-cached generation.

## Setup

```bash
# 1. Virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Install
pip install -r requirements.txt

# 3. Configure
copy .env.example .env         # then edit values (DB_*, JWT_SECRET_KEY, ...)

# 4. Create the MySQL database
#    mysql -u root -p -e "CREATE DATABASE social_ai_saas CHARACTER SET utf8mb4;"

# 5. Seed demo data (creates tables + demo users/workspaces/snapshots)
python seed.py

# 6. Run
python run.py                  # http://127.0.0.1:5000
```

### Background jobs (daily snapshots)

```bash
# Requires Redis running.
celery -A worker.celery_app.celery worker --loglevel=info
celery -A worker.celery_app.celery beat   --loglevel=info

# Or run the job once manually:
flask --app run.py run-snapshots
```

## Demo logins (after `python seed.py`)

| Role           | Email                | Password    |
| -------------- | -------------------- | ----------- |
| Platform admin | admin@saasapp.test   | Admin123    |
| Asha (Pro)     | asha@saasapp.test    | Password123 |
| Rahul (Agency) | rahul@saasapp.test   | Password123 |

## Testing

```bash
pip install pytest
pytest -q          # SQLite-backed; no MySQL required
```

## API surface

See [`docs/API.md`](docs/API.md) for the full route table, and
[`docs/DATABASE.md`](docs/DATABASE.md) for the schema. All routes are prefixed
with `/api`. Auth is `Authorization: Bearer <token>` plus `X-Workspace-Id` for
workspace-scoped endpoints.
