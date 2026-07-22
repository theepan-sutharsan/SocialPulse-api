"""Referrals blueprint (stretch) — /api/referrals."""

from flask import Blueprint

from app.controllers import referral_controller as ctrl
from app.middleware import login_required

referral_bp = Blueprint("referrals", __name__, url_prefix="/api/referrals")


@referral_bp.post("")
@login_required
def create_referral():
    return ctrl.create_referral()


@referral_bp.get("")
@login_required
def get_referrals():
    return ctrl.get_referrals()
