# views/callback.py
from flask import Blueprint, request, jsonify
import json
from models import db, Payment
from radius import activate_user

cb_bp = Blueprint("cb_bp", __name__)

@cb_bp.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    data = request.get_json() or {}
    stk  = data.get("Body", {}).get("stkCallback", {})
    result_code = stk.get("ResultCode")
    checkout_id = stk.get("CheckoutRequestID")

    # Lookup the payment
    payment = Payment.query.filter_by(checkout_request_id=checkout_id).first()
    if not payment:
        return jsonify({"error":"Payment not found"}), 404

    if result_code == 0:
        payment.status = 'success'
        db.session.commit()
        activate_user(payment)
    else:
        payment.status = 'failed'
        db.session.commit()

    return jsonify({"Result":"OK"}), 200
