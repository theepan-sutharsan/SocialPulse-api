# Architecture

## Request lifecycle

1. **Route** (`app/routes/*`) — thin blueprint handler, applies the
   `roles_required` / `login_required` decorator, delegates to a controller.
2. **Middleware** (`app/middleware.py`) — verifies the JWT, resolves the active
   workspace from `X-Workspace-Id`, validates membership + role, stores
   `current_workspace` / `current_member` on `flask.g`.
3. **Controller** (`app/controllers/*`) — validates payload, enforces workspace
   isolation (`filter_by(workspace_id=current_workspace.id)`), calls services,
   returns the standard response shape.
4. **Service** (`app/services/*`) — external integrations (AI providers,
   YouTube, Stripe/Razorpay) and domain jobs (snapshots). Controllers never
   import provider SDKs directly.
5. **Model** (`app/models/*`) — SQLAlchemy entity with `to_dict()`.

## Response conventions

- Create `201`: `{"message": "...", "<entity>": {...}}`
- List `200`: `{"<entities>": [...]}`
- Read `200`: `{"<entity>": {...}}`
- Validation `400`: `{"errors": [...]}`
- Business error: `{"error": "..."}` with an appropriate status
- Not found `404`: `{"error": "<Entity> not found."}`
- Credit exhausted `402`: `{"error": "AI credit limit reached. Upgrade your plan."}`

## AI provider fallback

`ai_service.generate()` tries the configured primary provider, then the next in
`[anthropic, openai, gemini]`. A cache (short TTL) serves identical
`(type, prompt_input)` pairs for free. With no external keys configured, a
deterministic local generator keeps the app fully functional for development.

## Background jobs

`worker/celery_app.py` binds Celery to the Flask app context. Beat schedules
`run_daily_snapshots` daily; each run inserts one `analytics_snapshots` row per
account (idempotent via the unique constraint).
