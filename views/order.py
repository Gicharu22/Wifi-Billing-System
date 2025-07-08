# views/order.py
from flask import Blueprint, request, jsonify
from mpesa import stk_push
from models import db, Payment
from app import PACKAGES

order_bp = Blueprint("order_bp", __name__)

@order_bp.route("/api/order", methods=["POST"])
def create_order():
    data       = request.get_json() or {}
    phone      = data.get("phone")
    package_id = data.get("package_id")
    if not phone or not package_id:
        return jsonify({"error": "phone and package_id are required"}), 400

    pkg = next((p for p in PACKAGES if p["id"]==package_id), None)
    if not pkg or not pkg["enabled"]:
        return jsonify({"error": "Invalid or disabled package"}), 400

    try:
        resp = stk_push(phone, pkg["price"], package_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Persist payment
    pr = Payment(
      checkout_request_id = resp["CheckoutRequestID"],
      merchant_request_id = resp["MerchantRequestID"],
      user_phone          = phone,
      package_id          = package_id,
      status              = 'pending'
    )
    db.session.add(pr)
    db.session.commit()

    return jsonify(resp), 202
