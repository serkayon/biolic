from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models import db, User, MachineLogin, OTP
import logging
from email_service import email_service

logger = logging.getLogger(__name__)
bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# =========================
# Register
# =========================
@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        required_fields = ['name', 'email', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        user = User(
            name=data['name'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Clear OTP if any
        OTP.query.filter_by(email=data['email']).delete()
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return jsonify({'error': 'Registration failed'}), 500

# =========================
# Login
# =========================
@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403
        
        machine_fingerprint = data.get('machine_fingerprint')
        mac_address = data.get('mac_address', '')
        
        existing_login = None
        if machine_fingerprint:
            existing_login = MachineLogin.query.filter_by(
                machine_fingerprint=machine_fingerprint
            ).first()
        if not existing_login:
            existing_login = MachineLogin.query.filter_by(mac_address=mac_address).first()
        
        if existing_login:
            existing_login.user_id = user.id
            existing_login.current_email = user.email
            existing_login.last_activity = datetime.utcnow()
        else:
            machine_login = MachineLogin(
                machine_id=data.get('machine_id', 'unknown'),
                mac_address=mac_address,
                machine_fingerprint=machine_fingerprint,
                user_id=user.id,
                current_email=user.email
            )
            db.session.add(machine_login)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return jsonify({'error': 'Login failed'}), 500

# =========================
# Logout
# =========================
@bp.route('/logout', methods=['POST'])
def logout():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        MachineLogin.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        return jsonify({'message': 'Logout successful'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return jsonify({'error': 'Logout failed'}), 500

# =========================
# Forgot Password
# =========================
@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Account not found'}), 404
        
        OTP.query.filter_by(email=email).delete()
        
        otp_code = email_service.generate_otp()
        otp_record = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        db.session.add(otp_record)
        db.session.commit()
        
        success, _ = email_service.send_otp_email(email, otp_code)
        
        if success:
            return jsonify({'message': 'OTP sent'}), 200
        else:
            return jsonify({'error': 'Email failed'}), 500
    
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return jsonify({'error': 'Server error'}), 500

# =========================
# Reset Password
# =========================
@bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        
        email = data.get('email')
        otp_code = data.get('otp')
        new_password = data.get('new_password')
        
        otp_record = OTP.query.filter_by(
            email=email,
            otp_code=otp_code
        ).first()
        
        if not otp_record or otp_record.is_expired():
            return jsonify({'error': 'Invalid or expired OTP'}), 400
        
        user = User.query.filter_by(email=email).first()
        user.set_password(new_password)
        
        db.session.delete(otp_record)
        db.session.commit()
        
        return jsonify({'message': 'Password reset successful'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return jsonify({'error': 'Reset failed'}), 500
