# mpesa.py

import os
from dotenv import load_dotenv

# Load .env immediately when this module is imported
load_dotenv()

import requests
import base64
import datetime
from dotenv import load_dotenv, find_dotenv
import os

# 1. Locate your .env file anywhere above the current folder
dotenv_path = find_dotenv()
print("🔍 .env found at:", dotenv_path)

# 2. Load its contents into os.environ
load_dotenv(dotenv_path)

# 3. Immediately print one key to verify
print("✔️ MPESA_KEY =", os.getenv("MPESA_KEY"))

print("✔️ MPESA_SECRET =", repr(os.getenv("MPESA_SECRET")))

# Redis is optional—provide a fallback URL
try:
    from redis import Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_cli = Redis.from_url(redis_url)
except Exception:
    redis_cli = None


def get_token():
    """
    Fetches (and caches) an OAuth access token from Safaricom Daraja.
    Caches in Redis under key "mpesa_token" with an expiry 50s before actual expiry.
    """
    if redis_cli:
        token = redis_cli.get("mpesa_token")
        if token:
            return token.decode()

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    consumer_key    = os.getenv("MPESA_KEY")
    consumer_secret = os.getenv("MPESA_SECRET")

    # Debug print to verify env values
    print("Using MPESA_KEY =", repr(consumer_key))
    print("Using MPESA_SECRET =", repr(consumer_secret))

    resp = requests.get(url, auth=(consumer_key, consumer_secret))
    resp.raise_for_status()
    data = resp.json()

    access_token = data.get("access_token")
    expires_in   = int(data.get("expires_in", 3600))

    if redis_cli and access_token:
        # Cache token slightly shorter than real expiry
        redis_cli.setex("mpesa_token", expires_in - 50, access_token)

    return access_token


def stk_push(phone: str, amount: float, package_id: str):
    """
    Initiates an STK Push to the user's phone.
    Returns the JSON response from Daraja.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    shortcode = os.getenv("MPESA_SHORTCODE")
    passkey   = os.getenv("MPESA_PASSKEY")

    raw      = f"{shortcode}{passkey}{timestamp}".encode("utf-8")
    password = base64.b64encode(raw).decode("utf-8")

    payload = {
        "BusinessShortCode": shortcode,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            amount,
        "PartyA":            phone,
        "PartyB":            shortcode,
        "PhoneNumber":       phone,
        "CallBackURL":       f"{os.getenv('DOMAIN')}/mpesa/callback",
        "AccountReference":  f"pkg-{package_id}",
        "TransactionDesc":   f"Payment for package {package_id}"
    }

    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type":  "application/json"
    }

    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    resp = requests.post(stk_url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()
