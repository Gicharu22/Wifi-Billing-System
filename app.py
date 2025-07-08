import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.DEBUG)
# 1) Load .env into os.environ
load_dotenv()

# 2) Create the Flask app and pull secret from env
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-to-a-random-secret")

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db  # the SQLAlchemy() instance

# initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# 3) In-memory package list (unchanged)
PACKAGES = [
    {"id": "2hr",   "label": "2 HRS Unlimited",   "price": 15,  "enabled": True},
    {"id": "4hr",   "label": "4 HRS Unlimited",   "price": 25,  "enabled": True},
    {"id": "6hr",   "label": "6 HRS Unlimited",   "price": 30,  "enabled": True},
    {"id": "12hr",  "label": "12 HRS Unlimited",  "price": 40,  "enabled": True},
    {"id": "24hr",  "label": "24 HRS Unlimited",  "price": 50,  "enabled": True},
    {"id": "2day",  "label": "2 Days Unlimited",  "price": 70,  "enabled": True},
    {"id": "3day",  "label": "3 Days Unlimited",  "price": 90,  "enabled": True},
    {"id": "7day",  "label": "7 Days Unlimited",  "price": 250, "enabled": True},
    {"id": "14day", "label": "14 Days Unlimited", "price": 400, "enabled": True},
    {"id": "30day", "label": "30 Days Unlimited", "price": 700, "enabled": True},
]

# 4) In-memory voucher list (unchanged)
VOUCHERS = []

# 5) In-memory settings, but now seeded from environment
SETTINGS = {
    # Payment Settings (fall back to your old defaults if env not set)
    "payment_gateway": os.getenv("PAYMENT_GATEWAY", "mpesa"),
    "api_key":         os.getenv("API_KEY", ""),
    "currency":        os.getenv("CURRENCY", "KES"),

    # Wi-Fi Parameters (just in case you want them here)
    "max_connections": int(os.getenv("MAX_CONNECTIONS", 10)),
    "session_timeout": int(os.getenv("SESSION_TIMEOUT", 3600)),   # in seconds
    "bandwidth_limit": int(os.getenv("BANDWIDTH_LIMIT", 0)),      # 0 = unlimited
}

# ---- PUBLIC USER ROUTES ----

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST" and "package" in request.form:
        pkg_id = request.form["package"]
        phone = request.form["phone"]
        return redirect(url_for("confirmation", pkg_id=pkg_id, phone=phone))
    return render_template("index.html", packages=PACKAGES)

@app.route("/confirmation")
def confirmation():
    pkg_id = request.args.get("pkg_id")
    phone = request.args.get("phone")
    pkg = next((p for p in PACKAGES if p["id"] == pkg_id), None)
    return render_template("confirmation.html", pkg=pkg, phone=phone)

@app.route("/reconnect", methods=["POST"])
def reconnect():
    mpesa_code = request.form.get("mpesa_code")
    if not mpesa_code:
        flash("Please enter your M-Pesa transaction code.", "error")
        return redirect(url_for("index"))
    flash(f"Transaction {mpesa_code} received. Reconnecting...", "success")
    return redirect(url_for("index"))

@app.route("/voucher", methods=["POST"])
def voucher():
    voucher_code = request.form.get("voucher_code")
    if not voucher_code:
        flash("Please enter your voucher code.", "error")
        return redirect(url_for("index"))
    flash(f"Voucher {voucher_code} activated.", "success")
    return redirect(url_for("index"))

# ---- ADMIN AUTH ----

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (request.form.get("username") == os.getenv("ADMIN_USER", "admin") and
            request.form.get("password") == os.getenv("ADMIN_PASS", "password")):
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "error")
    return render_template("admin_login.html")

# ---- ADMIN DASHBOARD ----

@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():
    hourly = ["2 HRS Unlimited", "4 HRS Unlimited", "6 HRS Unlimited",
              "12 HRS Unlimited", "24 HRS Unlimited"]
    daily  = ["2 Days Unlimited", "3 Days Unlimited", "7 Days Unlimited",
              "14 Days Unlimited", "30 Days Unlimited"]
    stats = {
        "income_today":    f"{SETTINGS['currency']} 00",
        "monthly_income":  f"{SETTINGS['currency']} 00",
        "active_subs":     0,
        "all_subs":        0,
        "plan_counts_hours": { key: 0 for key in hourly },
        "plan_counts_days":  { key: 0 for key in daily },
    }
    return render_template("admin.html", stats=stats, section="dashboard")

# ---- ADMIN PACKAGES ----

@app.route("/admin/packages", methods=["GET", "POST"])
def admin_packages():
    global PACKAGES
    if request.method == "POST":
        action = request.form.get("action")
        if action == "delete":
            pkg_id = request.form.get("pkg_id")
            PACKAGES = [p for p in PACKAGES if p["id"] != pkg_id]
            flash(f"Deleted package {pkg_id}.", "success")
        elif action == "add":
            new_label = request.form.get("new_label", "").strip()
            new_price = request.form.get("new_price", "").strip()
            if not (new_label and new_price.isdigit()):
                flash("Label and numeric price are required.", "error")
            else:
                PACKAGES.append({
                    "id":      new_label.lower().replace(" ", ""),
                    "label":   new_label,
                    "price":   int(new_price),
                    "enabled": True
                })
                flash(f"Added new package: {new_label}", "success")
        return redirect(url_for("admin_packages"))

    return render_template("admin_packages.html", packages=PACKAGES, section="packages")

# ---- ADMIN VOUCHERS ----

@app.route("/admin/vouchers", methods=["GET", "POST"])
def admin_vouchers():
    global VOUCHERS
    if request.method == "POST":
        action = request.form.get("action")
        if action == "generate":
            code    = request.form.get("voucher_code", "").strip()
            expires = request.form.get("expires_date", "").strip()
            time    = request.form.get("expires_time", "").strip()
            if code and expires and time:
                combined = f"{expires}T{time}"
                VOUCHERS.append({
                    "code":       code,
                    "expires_on": combined
                })
                flash(f"Voucher {code} generated.", "success")
            else:
                flash("Code, expiration date, and time are required.", "error")
        return redirect(url_for("admin_vouchers"))

    return render_template("admin_voucher.html", vouchers=VOUCHERS, section="vouchers")

# ---- ADMIN SETTINGS ----

@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    global SETTINGS
    if request.method == "POST":
        # Company Info
        SETTINGS["company_name"]    = request.form.get("company_name", "").strip()
        SETTINGS["company_address"] = request.form.get("company_address", "").strip()
        SETTINGS["company_email"]   = request.form.get("company_email", "").strip()
        # Payment Settings
        SETTINGS["payment_gateway"] = request.form.get("payment_gateway", SETTINGS["payment_gateway"])
        SETTINGS["api_key"]         = request.form.get("api_key", SETTINGS["api_key"]).strip()
        SETTINGS["currency"]        = request.form.get("currency", SETTINGS["currency"]).strip()
        # Wi-Fi Parameters
        SETTINGS["max_connections"] = int(request.form.get("max_connections", SETTINGS["max_connections"]))
        SETTINGS["session_timeout"] = int(request.form.get("session_timeout", SETTINGS["session_timeout"]))
        SETTINGS["bandwidth_limit"] = int(request.form.get("bandwidth_limit", SETTINGS["bandwidth_limit"]))

        flash("Settings saved.", "success")
        return redirect(url_for("admin_settings"))

    return render_template(
        "settings.html",
        settings=SETTINGS,
        section="settings"
    )
# Register your API blueprints:
from views.order     import order_bp
from views.callback  import cb_bp
# (if you made reconnect.py) from views.reconnect import rec_bp

app.register_blueprint(order_bp)     # mounts /api/order
app.register_blueprint(cb_bp)        # mounts /mpesa/callback
# app.register_blueprint(rec_bp)     # mounts /api/reconnect


# ---- RUN ----

if __name__ == "__main__":
    # use debug mode if FLASK_ENV=development
    debug_mode = os.getenv("FLASK_ENV", "production") == "development"
    app.run(debug=debug_mode)
