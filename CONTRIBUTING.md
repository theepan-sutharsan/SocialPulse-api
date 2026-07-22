# Contributing

## Conventions

- Follow the existing layout: `models` / `controllers` / `routes` / `services`.
- Keep route handlers thin; business logic lives in controllers.
- Every tenant-owned query must filter by `current_workspace.id`.
- Match response shapes (`errors` array for validation, `error` string otherwise).
- All AI calls go through `app/services/ai_service.py`; all billing through
  `app/services/billing_service.py`. Never import provider SDKs in controllers.

## Commit style

Conventional Commits: `feat(scope): ...`, `fix: ...`, `chore: ...`,
`docs: ...`, `test: ...`, `refactor: ...`.

## Before opening a PR

```bash
ruff check app worker tests
pytest -q
```
