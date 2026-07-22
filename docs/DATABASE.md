# Database Schema

MySQL (SQLAlchemy). Every tenant-owned table carries `workspace_id`.

```
users ── workspace_members ── workspaces      (users <-> workspaces: MANY-TO-MANY)
                                   ├── social_accounts
                                   │        └── analytics_snapshots  (1 row/account/day)
                                   ├── ai_generations ── scheduled_posts
                                   ├── subscriptions (1:1)
                                   ├── credit_usages
                                   └── notifications
users → referrals (stretch)
```

## Tables

- **users** — `id, email (unique), password (hashed), full_name, is_platform_admin, is_active, created_at`
- **workspaces** — `id, name, slug (unique), plan_tier, is_agency, bio, tagline, brand_color, logo_url, is_white_label, created_at`
- **workspace_members** — `id, user_id, workspace_id, role, invited_at, joined_at, created_at` · UNIQUE(`user_id`, `workspace_id`)
- **social_accounts** — `id, workspace_id, platform, handle, is_demo, access_token (enc), refresh_token (enc), connected_at, created_at` · UNIQUE(`workspace_id`, `platform`, `handle`)
- **analytics_snapshots** — `id, social_account_id, snapshot_date, follower_count, view_count, engagement_rate, created_at` · UNIQUE(`social_account_id`, `snapshot_date`)
- **ai_generations** — `id, workspace_id, social_account_id?, generation_type, prompt_input, result, provider, credits_used, created_at`
- **scheduled_posts** — `id, workspace_id, ai_generation_id?, social_account_id, caption, scheduled_at, status, created_at`
- **subscriptions** — `id, workspace_id (unique), plan_tier, billing_provider, provider_customer_id, provider_subscription_id, status, current_period_end, created_at`
- **credit_usages** — `id, workspace_id, period_start, credits_allotted, credits_used, created_at` · UNIQUE(`workspace_id`, `period_start`)
- **notifications** — `id, user_id, workspace_id, type, message, is_read, created_at`
- **referrals** — `id, referrer_id, referred_email, status, created_at`
