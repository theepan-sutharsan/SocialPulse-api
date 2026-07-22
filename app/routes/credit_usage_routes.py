"""Credit usage blueprint — /api/credit-usage."""

from flask import Blueprint

from app.controllers import credit_usage_controller as ctrl
from app.middleware import ALL_ROLES, roles_required

credit_usage_bp = Blueprint("credit_usage", __name__, url_prefix="/api/credit-usage")


@credit_usage_bp.get("/current")
@roles_required(*ALL_ROLES)
def current_usage():
    return ctrl.get_current_usage()
