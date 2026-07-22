"""Dashboard blueprint — /api/me."""

from flask import Blueprint

from app.controllers import dashboard_controller as ctrl
from app.middleware import ALL_ROLES, roles_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/me")


@dashboard_bp.get("/dashboard")
@roles_required(*ALL_ROLES)
def dashboard():
    return ctrl.get_dashboard()
