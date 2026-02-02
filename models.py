from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from sqlalchemy.dialects.postgresql import UUID

db = SQLAlchemy()

# =========================
# User
# =========================
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(512), nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    machines = db.relationship('Machine', backref='user', lazy=True, cascade='all, delete-orphan')
    machine_logins = db.relationship('MachineLogin', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

# =========================
# Machine
# =========================
class Machine(db.Model):
    __tablename__ = 'machines'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    
    mac_address = db.Column(db.String(255), nullable=False)
    machine_name = db.Column(db.String(255), nullable=False)
    machine_id = db.Column(db.String(255), unique=True, nullable=False)
    os_name = db.Column(db.String(255), nullable=True)
    os_version = db.Column(db.String(255), nullable=True)
    processor = db.Column(db.String(255), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    registered_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'mac_address': self.mac_address,
            'machine_name': self.machine_name,
            'machine_id': self.machine_id,
            'os_name': self.os_name,
            'os_version': self.os_version,
            'processor': self.processor,
            'is_active': self.is_active,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
        }

# =========================
# Machine Login
# =========================
class MachineLogin(db.Model):
    __tablename__ = 'machine_logins'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    mac_address = db.Column(db.String(255), nullable=False, index=True)
    
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    current_email = db.Column(db.String(255), nullable=False)
    
    machine_fingerprint = db.Column(db.String(64), nullable=True, index=True)
    fingerprint_short = db.Column(db.String(16), nullable=True)
    fingerprint_stability = db.Column(db.Integer, default=0)
    fingerprint_components = db.Column(db.JSON, nullable=True)
    
    machine_name = db.Column(db.String(255), nullable=True)
    os_name = db.Column(db.String(255), nullable=True)
    os_version = db.Column(db.String(255), nullable=True)
    processor = db.Column(db.String(255), nullable=True)
    
    logged_in_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    last_activity = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'machine_id': self.machine_id,
            'mac_address': self.mac_address,
            'machine_fingerprint': self.machine_fingerprint,
            'fingerprint_short': self.fingerprint_short,
            'fingerprint_stability': self.fingerprint_stability,
            'user_id': str(self.user_id),
            'current_email': self.current_email,
            'machine_name': self.machine_name,
            'os_name': self.os_name,
            'os_version': self.os_version,
            'processor': self.processor,
            'logged_in_at': self.logged_in_at.isoformat() if self.logged_in_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'fingerprint_components': self.fingerprint_components,
        }

# =========================
# License
# =========================
class License(db.Model):
    __tablename__ = 'licenses'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    machine_fingerprint = db.Column(db.String(64), unique=True, nullable=False, index=True)
    fingerprint_short = db.Column(db.String(16), nullable=True)
    fingerprint_stability = db.Column(db.Integer, default=0)
    
    mac_address = db.Column(db.String(255), nullable=True, index=True)
    machine_id = db.Column(db.String(255), nullable=True)
    machine_name = db.Column(db.String(255), nullable=True)
    
    fingerprint_components = db.Column(db.JSON, nullable=True)
    
    plan_type = db.Column(db.String(50), nullable=False)
    plan_name = db.Column(db.String(255), nullable=False)
    plan_price = db.Column(db.String(50), nullable=True)
    
    activated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    
    is_active = db.Column(db.Boolean, default=True)
    
    last_verified_fingerprint = db.Column(db.DateTime(timezone=True), nullable=True)
    fingerprint_mismatch_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    upgraded_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'license_id': self.license_id,
            'machine_fingerprint': self.machine_fingerprint,
            'fingerprint_short': self.fingerprint_short,
            'fingerprint_stability': self.fingerprint_stability,
            'mac_address': self.mac_address,
            'machine_id': self.machine_id,
            'machine_name': self.machine_name,
            'plan_type': self.plan_type,
            'plan_name': self.plan_name,
            'plan_price': self.plan_price,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'upgraded_at': self.upgraded_at.isoformat() if self.upgraded_at else None,
            'fingerprint_stability_score': self.fingerprint_stability,
        }

# =========================
# User Session
# =========================
class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    
    machine_id = db.Column(db.String(255), nullable=False)
    machine_name = db.Column(db.String(255), nullable=False)
    mac_address = db.Column(db.String(255), nullable=False)
    os_name = db.Column(db.String(255), nullable=True)
    os_version = db.Column(db.String(255), nullable=True)
    
    login_token = db.Column(db.String(512), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True)
    
    logged_in_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    logged_out_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_activity = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'machine_id': self.machine_id,
            'machine_name': self.machine_name,
            'mac_address': self.mac_address,
            'os_name': self.os_name,
            'os_version': self.os_version,
            'logged_in_at': self.logged_in_at.isoformat() if self.logged_in_at else None,
            'logged_out_at': self.logged_out_at.isoformat() if self.logged_out_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active
        }

# =========================
# OTP
# =========================
class OTP(db.Model):
    __tablename__ = 'otps'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    
    is_verified = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }
