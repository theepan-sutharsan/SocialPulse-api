# Seeding & Demo Data

Run `python seed.py` to create the demo world (idempotent — it skips if the
platform admin already exists).

## What it creates

- **Platform admin** — `admin@saasapp.test / Admin123`
- **Asha (Pro)** — `asha@saasapp.test / Password123`
  - `Asha Creates` workspace, YouTube (live-shaped) + Instagram (Demo Mode)
- **Rahul (Agency)** — `rahul@saasapp.test / Password123`
  - `Rahul Agency` + `Client One` (owner) + `Client Two` (editor) — demonstrates
    the many-to-many `workspace_members` relationship
- 30 days of backfilled `analytics_snapshots` per account
- One AI generation, one scheduled post, and partially-consumed credit ledgers

## Reset

`python scripts/reset_db.py` drops and recreates all tables (dev only).
