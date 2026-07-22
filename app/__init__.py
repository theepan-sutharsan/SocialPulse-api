"""Application factory.

Wires configuration, extensions (SQLAlchemy, JWT, CORS, Celery, Sentry),
JWT identity/lookup callbacks, global error handlers, and blueprint
registration. Import all models before ``db.create_all()`` so every table is
created on first boot.
"""

import logging

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.config import Config
from app.extensions import celery, db, jwt


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    _configure_logging(app)
    _init_sentry(app)
    _init_extensions(app)
    _register_jwt_callbacks()
    _register_error_handlers(app)
    _register_blueprints(app)
    _init_database(app)
    _register_cli(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "social-ai-saas-api"}

    return app


def _register_cli(app: Flask) -> None:
    @app.cli.command("run-snapshots")
    def run_snapshots():
        """Run the daily analytics snapshot job once (manual trigger)."""
        from app.services import snapshot_service

        result = snapshot_service.run_daily_snapshots()
        app.logger.info("run-snapshots result: %s", result)
        print(f"Snapshots complete: {result}")


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.config.get("FLASK_DEBUG") else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _init_sentry(app: Flask) -> None:
    dsn = app.config.get("SENTRY_DSN")
    if not dsn:
        return
    try:  # Sentry is optional; never let it break boot.
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(dsn=dsn, integrations=[FlaskIntegration()], traces_sample_rate=0.1)
        app.logger.info("Sentry error monitoring enabled.")
    except Exception as exc:  # pragma: no cover - defensive
        app.logger.warning("Sentry init failed: %s", exc)


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    jwt.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        expose_headers=["Content-Disposition"],
    )
    if celery is not None:
        celery.conf.update(
            broker_url=app.config["REDIS_URL"],
            result_backend=app.config["REDIS_URL"],
            task_ignore_result=False,
            timezone="UTC",
        )


def _register_jwt_callbacks() -> None:
    from app.models.user_model import User

    @jwt.user_identity_loader
    def _identity(user):
        return str(getattr(user, "id", user))

    @jwt.user_lookup_loader
    def _lookup(_header, data):
        try:
            return db.session.get(User, int(data["sub"]))
        except (TypeError, ValueError):
            return None

    @jwt.unauthorized_loader
    def _unauthorized(reason):
        return jsonify({"error": "Missing or invalid authorization token."}), 401

    @jwt.invalid_token_loader
    def _invalid(reason):
        return jsonify({"error": "Invalid authorization token."}), 401

    @jwt.expired_token_loader
    def _expired(_header, _payload):
        return jsonify({"error": "Token has expired. Please log in again."}), 401


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(OperationalError)
    def _db_operational(err):  # DB unreachable / connection dropped
        db.session.rollback()
        app.logger.error("Database operational error: %s", err)
        return jsonify({"error": "Database is temporarily unavailable."}), 503

    @app.errorhandler(ProgrammingError)
    def _db_programming(err):  # missing table / bad SQL
        db.session.rollback()
        app.logger.error("Database programming error: %s", err)
        return jsonify({"error": "Database schema error. Run migrations/seed."}), 500

    @app.errorhandler(404)
    def _not_found(_err):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(405)
    def _method_not_allowed(_err):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def _server_error(err):
        db.session.rollback()
        app.logger.exception("Unhandled server error: %s", err)
        return jsonify({"error": "Internal server error."}), 500


def _register_blueprints(app: Flask) -> None:
    from app.routes import register_blueprints

    register_blueprints(app)


def _init_database(app: Flask) -> None:
    # Importing the models package registers every table on the metadata.
    from app import models  # noqa: F401

    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables ensured.")
        except (OperationalError, ProgrammingError) as exc:
            app.logger.warning("Skipping create_all (database not ready): %s", exc)
