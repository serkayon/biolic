from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models import db, OTP
from email_service import email_service
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('otp', __name__, url_prefix='/api/otp')

# =========================
# Send OTP
# =========================
@bp.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to email for verification - 5 minute expiry"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email address'}), 400
        
        # Check if email already has a pending OTP
        existing_otp = OTP.query.filter_by(email=email, is_verified=False).first()
        if existing_otp and not existing_otp.is_expired():
            return jsonify({
                'error': 'OTP already sent. Please check your inbox.',
                'email': email
            }), 400
        
        # Delete old OTPs
        OTP.query.filter_by(email=email).delete()
        db.session.commit()
        
        # Generate OTP
        otp_code = email_service.generate_otp()
        
        # Create OTP record (5 minute expiry)
        otp_record = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        db.session.add(otp_record)
        db.session.commit()
        
        # Send OTP email
        success, message = email_service.send_otp_email(email, otp_code)
        
        if success:
            logger.info(f"OTP sent to {email}")
            return jsonify({
                'message': 'OTP sent successfully',
                'email': email
            }), 200
        else:
            db.session.delete(otp_record)
            db.session.commit()
            logger.error(f"OTP email failed for {email}")
            return jsonify({'error': 'Failed to send OTP'}), 500
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"send_otp error: {e}")
        return jsonify({'error': 'Server error'}), 500

# =========================
# Verify OTP
# =========================
@bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and check against database"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        otp_code = data.get('otp', '').strip()
        
        if not email or not otp_code:
            return jsonify({'error': 'Email and OTP required'}), 400
        
        otp_record = OTP.query.filter_by(
            email=email,
            is_verified=False
        ).first()
        
        if not otp_record:
            return jsonify({
                'error': 'No OTP found. Please request again.',
                'verified': False
            }), 400
        
        if otp_record.is_expired():
            db.session.delete(otp_record)
            db.session.commit()
            return jsonify({
                'error': 'OTP expired. Request new one.',
                'verified': False
            }), 400
        
        if otp_record.otp_code != otp_code:
            otp_record.failed_attempts += 1
            
            if otp_record.failed_attempts >= 5:
                db.session.delete(otp_record)
                db.session.commit()
                return jsonify({
                    'error': 'Too many attempts. Request new OTP.',
                    'verified': False
                }), 400
            
            db.session.commit()
            return jsonify({
                'error': f'Invalid OTP. {5 - otp_record.failed_attempts} attempts left.',
                'verified': False
            }), 400
        
        # Mark verified
        otp_record.is_verified = True
        db.session.commit()
        
        logger.info(f"OTP verified for {email}")
        
        return jsonify({
            'message': 'OTP verified successfully',
            'verified': True,
            'email': email
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"verify_otp error: {e}")
        return jsonify({'error': 'Server error'}), 500
