# Testing

The suite is SQLite-backed and needs no MySQL, Redis, or provider keys.

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Layout

- `tests/conftest.py` — app/client/auth fixtures on a temp SQLite database.
- `tests/helpers.py` — `register`, `connect_demo`, `set_plan` helpers.
- `tests/test_*.py` — one module per feature area (auth, workspaces, members,
  social accounts, history/grade, AI, credits, scheduling, billing, media kit,
  admin, dashboard, notifications, referrals, export) plus service-layer and
  middleware tests.

## Notes

- AI tests exercise the deterministic local fallback (no API keys).
- Billing tests use simulated checkout (no Stripe/Razorpay keys).
- Credit-metering tests verify deduction, cache-free behaviour, and the `402`
  exhaustion path.
