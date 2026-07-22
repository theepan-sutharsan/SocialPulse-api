# Deployment

## Docker Compose (local full stack)

```bash
cp .env.example .env    # set secrets
docker compose up --build
# API on :5000, MySQL on :3306, Redis on :6379, plus worker + beat
```

## Manual / VM

1. Provision MySQL 8 and Redis.
2. `pip install -r requirements.txt`
3. Set env vars (see `.env.example`).
4. Run migrations/tables: `python seed.py` (or `flask --app run.py shell` then `db.create_all()`).
5. Serve with gunicorn: `gunicorn -c gunicorn.conf.py run:app`
6. Start workers:
   - `celery -A worker.celery_app.celery worker --loglevel=info`
   - `celery -A worker.celery_app.celery beat --loglevel=info`

## Production checklist

- [ ] Strong `SECRET_KEY`, `JWT_SECRET_KEY`, and a dedicated `ENCRYPTION_KEY`.
- [ ] Real provider keys (Anthropic/OpenAI/Google), Stripe/Razorpay, YouTube OAuth.
- [ ] `SENTRY_DSN` set for error monitoring.
- [ ] `FLASK_DEBUG=0`.
- [ ] Restrict CORS origins to the deployed frontend.
- [ ] Managed MySQL with backups; Redis with persistence for Celery.
