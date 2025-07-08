# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Package(db.Model):
    id            = db.Column(db.String(20), primary_key=True)
    label         = db.Column(db.String(64), nullable=False)
    price         = db.Column(db.Numeric(10,2), nullable=False)
    duration_mins = db.Column(db.Integer, nullable=False)
    enabled       = db.Column(db.Boolean, default=True)

class User(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    phone_number    = db.Column(db.String(20), unique=True, nullable=False)
    mpesa_code      = db.Column(db.String(16), unique=True)
    current_pkg_id  = db.Column(db.String(20), db.ForeignKey('package.id'))
    connected_at    = db.Column(db.DateTime)

class Payment(db.Model):
    id                   = db.Column(db.Integer, primary_key=True)
    checkout_request_id  = db.Column(db.String(64), unique=True, nullable=False)
    merchant_request_id  = db.Column(db.String(64), nullable=False)
    user_phone           = db.Column(db.String(20), nullable=False)
    package_id           = db.Column(db.String(20), db.ForeignKey('package.id'), nullable=False)
    status               = db.Column(db.Enum('pending','success','failed', name='pay_status'),
                                           default='pending')
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)

class Voucher(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    code        = db.Column(db.String(16), unique=True, nullable=False)
    package_id  = db.Column(db.String(20), db.ForeignKey('package.id'), nullable=False)
    expires_at  = db.Column(db.DateTime, nullable=False)
    used        = db.Column(db.Boolean, default=False)
