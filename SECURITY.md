# Security

## Reporting

Please report vulnerabilities privately to the maintainers rather than opening a
public issue.

## Practices in this codebase

- Passwords hashed with Werkzeug (`generate_password_hash`).
- JWT Bearer auth; tokens carry only the user id (`sub`).
- OAuth tokens encrypted at rest with Fernet (`app/utils/security.py`).
- Multi-tenant isolation enforced server-side on every query.
- Billing webhooks verify provider signatures before mutating state.
- Secrets are read from the environment; `.env` is git-ignored.
