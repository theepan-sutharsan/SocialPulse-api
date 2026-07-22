"""Referrals (stretch): create a referral invite and list my referrals."""

from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models.referral_model import Referral
from app.utils import is_valid_email


def create_referral():
    data = request.get_json(silent=True) or {}
    email = (data.get("referred_email") or "").strip().lower()
    if not is_valid_email(email):
        return jsonify({"errors": ["A valid referred_email is required."]}), 400
    if Referral.query.filter_by(referrer_id=current_user.id, referred_email=email).first():
        return jsonify({"error": "You have already referred this email."}), 409
    try:
        referral = Referral(referrer_id=current_user.id, referred_email=email)
        db.session.add(referral)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not create referral."}), 500
    return jsonify({"message": "Referral created.", "referral": referral.to_dict()}), 201


def get_referrals():
    referrals = (
        Referral.query.filter_by(referrer_id=current_user.id)
        .order_by(Referral.created_at.desc())
        .all()
    )
    return jsonify({"referrals": [r.to_dict() for r in referrals]}), 200
