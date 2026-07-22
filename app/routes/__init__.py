"""Blueprint registry — wires every feature blueprint onto the app."""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.routes.ai_generation_routes import ai_generation_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.billing_routes import billing_bp
    from app.routes.credit_usage_routes import credit_usage_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.generate_routes import generate_bp
    from app.routes.media_kit_routes import media_kit_bp
    from app.routes.notification_routes import notification_bp
    from app.routes.platform_admin_routes import platform_admin_bp
    from app.routes.referral_routes import referral_bp
    from app.routes.scheduled_post_routes import scheduled_post_bp
    from app.routes.social_account_routes import social_account_bp
    from app.routes.workspace_routes import workspace_bp

    for blueprint in (
        auth_bp,
        workspace_bp,
        social_account_bp,
        generate_bp,
        ai_generation_bp,
        credit_usage_bp,
        scheduled_post_bp,
        billing_bp,
        media_kit_bp,
        platform_admin_bp,
        dashboard_bp,
        notification_bp,
        referral_bp,
    ):
        app.register_blueprint(blueprint)
