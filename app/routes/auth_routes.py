"""Authentication blueprint — /api/auth."""

from flask import Blueprint

from app.controllers import auth_controller
from app.middleware import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    return auth_controller.register()


@auth_bp.post("/login")
def login():
    return auth_controller.login()


@auth_bp.post("/logout")
@login_required
def logout():
    return auth_controller.logout()


@auth_bp.get("/profile")
@login_required
def get_profile():
    return auth_controller.get_profile()


@auth_bp.put("/profile")
@login_required
def update_profile():
    return auth_controller.update_profile()
