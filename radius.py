# radius.py
import os
import random
import string
from datetime import datetime, timedelta
from celery import Celery
from models import db, User, Package

# Celery setup
celery = Celery(__name__, broker=os.getenv("REDIS_URL"))

# Determine DB mode and optionally connect to Postgres for FreeRADIUS
DATABASE_URL = os.getenv("DATABASE_URL", "")
pg = None
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    try:
        import psycopg2
        pg = psycopg2.connect(DATABASE_URL)
        print("✅ Connected to Postgres for FreeRADIUS integration.")
    except Exception as e:
        print("❌ Failed to connect to Postgres for FreeRADIUS:", e)
        pg = None
else:
    print("⚠️  Running in non-Postgres mode—skipping FreeRADIUS activation (dev mode).")


def activate_user(payment):
    """
    Activates a user's Wi-Fi session:
    - Creates or updates a User record
    - Generates a reconnect code
    - Upserts into FreeRADIUS radcheck (Postgres only)
    - Schedules a revoke task
    """
    # 1) Ensure a User record exists
    user = User.query.filter_by(phone_number=payment.user_phone).first()
    if not user:
        user = User(phone_number=payment.user_phone)
        db.session.add(user)
        db.session.commit()

    # 2) Assign selected package and generate reconnect code
    pkg = Package.query.get(payment.package_id)
    user.current_pkg_id = pkg.id
    user.connected_at = datetime.utcnow()
    user.mpesa_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    db.session.commit()

    # 3) Upsert into FreeRADIUS radcheck table if Postgres is available
    if pg:
        expiry = datetime.utcnow() + timedelta(minutes=pkg.duration_mins)
        with pg.cursor() as cur:
            cur.execute(
                """
                INSERT INTO radcheck(username, attribute, op, value)
                VALUES (%s, 'Cleartext-Password', ':=', %s)
                ON CONFLICT (username, attribute) DO UPDATE SET value = EXCLUDED.value;
                """,
                (user.phone_number, user.mpesa_code)
            )
            pg.commit()
        # 4) Schedule automatic revocation
        revoke_user.apply_async((user.phone_number,), eta=expiry)
    else:
        # Development stub: log instead of actual DB operation
        print(f"🔔 [DEV] Would upsert radcheck for {user.phone_number} with code {user.mpesa_code}")


@celery.task
def revoke_user(phone):
    """
    Revokes Wi-Fi access by removing the radcheck entry.
    """
    if pg:
        with pg.cursor() as cur:
            cur.execute("DELETE FROM radcheck WHERE username=%s", (phone,))
            pg.commit()
        print(f"⏱️  Revoked Wi-Fi for {phone}")
    else:
        print(f"🔔 [DEV] Would revoke radcheck for {phone}")
