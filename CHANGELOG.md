# Changelog

All notable changes to the API are documented here.

## [1.0.0] — 2026-07-22

### Added
- Multi-tenant workspaces with a `workspace_members` many-to-many junction.
- JWT auth (register creates a default workspace + owner membership + credits).
- Social account connect flow: live YouTube OAuth + Instagram/TikTok/X Demo Mode.
- Daily `analytics_snapshots` time-series + growth history, grade and milestone.
- Multi-provider AI generation (caption/hashtags/idea/viral-score/sentiment)
  with fallback, caching, and monthly credit metering.
- Content calendar (scheduled posts), media kit, notifications, referrals.
- Billing via Stripe + Razorpay with signature-verified webhooks.
- CSV + PDF export for Pro/Agency tiers.
- Celery worker + beat for the daily snapshot job.
- Full pytest suite and seed script.
