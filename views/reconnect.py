# views/reconnect.py
from flask import Blueprint, request, jsonify, flash, redirect, url_for

rec_bp = Blueprint("rec_bp", __name__)

@rec_bp.route("/api/reconnect", methods=["POST"])
def reconnect_api():
    data = request.get_json() or {}
    phone = data.get("phone")
    code  = data.get("code")
    # TODO: validate code against DB or in-memory, reactivate session
    return jsonify({"message": "Reconnect endpoint hit"}), 200
