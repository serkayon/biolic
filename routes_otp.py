from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from models import db, OTP
from email_service import email_service
from email_worker import email_queue
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('otp', __name__, url_prefix='/api/otp')

@bp.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'error': 'Email required'}), 400

        existing = OTP.query.filter_by(email=email, is_verified=False).first()
        if existing and not existing.is_expired():
            return jsonify({'error': 'OTP already sent'}), 400

        OTP.query.filter_by(email=email).delete()
        db.session.commit()

        otp_code = email_service.generate_otp()

        otp = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )

        db.session.add(otp)
        db.session.commit()

        email_queue.put((email, otp_code))

        return jsonify({'message': 'OTP queued'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return jsonify({'error': 'Server error'}), 500


@bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        otp_code = data.get('otp')

        otp = OTP.query.filter_by(email=email, is_verified=False).first()

        if not otp:
            return jsonify({'error': 'No OTP'}), 400

        if otp.is_expired():
            db.session.delete(otp)
            db.session.commit()
            return jsonify({'error': 'Expired'}), 400

        if otp.otp_code != otp_code:
            otp.failed_attempts += 1
            db.session.commit()
            return jsonify({'error': 'Invalid'}), 400

        otp.is_verified = True
        db.session.commit()
        return jsonify({'verified': True}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return jsonify({'error': 'Server error'}), 500
