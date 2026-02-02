from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models import db, User, License
from encryption import LicenseEncryption
import uuid
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('subscriptions', __name__, url_prefix='/api/subscriptions')

# =========================
# Plan configurations
# =========================
PLANS = {
    'trial': {
        'name': 'Radar Pro Trial',
        'duration_days': 7,
        'price': '₹0'
    },
    '1month': {
        'name': 'Radar Pro',
        'duration_days': 30,
        'price': '₹399'
    },
    '1year': {
        'name': 'Radar Pro Plus',
        'duration_days': 365,
        'price': '₹3999'
    }
}

# =========================
# Activate License
# =========================
@bp.route('/activate', methods=['POST'])
def activate_license():
    try:
        data = request.get_json()

        # user_id is now manual
        user_id = data.get('user_id')
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Invalid user'}), 401

        required_fields = ['machine_fingerprint', 'plan_type']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        if data['plan_type'] not in PLANS:
            return jsonify({'error': 'Invalid plan type'}), 400

        machine_fingerprint = data['machine_fingerprint']
        if len(machine_fingerprint) != 64:
            return jsonify({'error': 'Invalid fingerprint format'}), 400

        existing_license = License.query.filter_by(
            machine_fingerprint=machine_fingerprint
        ).first()

        # One trial per machine
        if data['plan_type'] == 'trial' and existing_license:
            return jsonify({
                'error': 'Trial already used',
                'allowed_plans': ['1month', '1year'],
                'code': 'TRIAL_ALREADY_USED'
            }), 409

        plan_config = PLANS[data['plan_type']]
        activated_at = datetime.utcnow()
        expiry_date = activated_at + timedelta(days=plan_config['duration_days'])

        if existing_license:
            # Upgrade
            existing_license.plan_type = data['plan_type']
            existing_license.plan_name = plan_config['name']
            existing_license.plan_price = plan_config['price']
            existing_license.activated_at = activated_at
            existing_license.expiry_date = expiry_date
            existing_license.is_active = True
            existing_license.upgraded_at = activated_at
            existing_license.updated_at = activated_at
            existing_license.fingerprint_stability = data.get('fingerprint_stability', 0)
            existing_license.fingerprint_components = data.get('fingerprint_components')
            existing_license.last_verified_fingerprint = activated_at
            license_id = existing_license.license_id
        else:
            # New license
            license_id = f"LIC-{uuid.uuid4().hex[:12].upper()}"
            license_obj = License(
                license_id=license_id,
                machine_fingerprint=machine_fingerprint,
                fingerprint_short=data.get('fingerprint_short'),
                fingerprint_stability=data.get('fingerprint_stability', 0),
                fingerprint_components=data.get('fingerprint_components'),
                mac_address=data.get('mac_address'),
                machine_id=data.get('machine_id'),
                machine_name=data.get('machine_name'),
                plan_type=data['plan_type'],
                plan_name=plan_config['name'],
                plan_price=plan_config['price'],
                activated_at=activated_at,
                expiry_date=expiry_date,
                is_active=True,
                last_verified_fingerprint=activated_at
            )
            db.session.add(license_obj)

        db.session.commit()

        # Encrypted response
        encrypted_response = LicenseEncryption.encrypt_license_data({
            'license_id': license_id,
            'activated_at': activated_at.isoformat(),
            'expiry_date': expiry_date.isoformat(),
            'plan_name': plan_config['name'],
            'plan_type': data['plan_type'],
            'machine_fingerprint': machine_fingerprint,
            'fingerprint_short': data.get('fingerprint_short', machine_fingerprint[:16]),
            'fingerprint_stability': data.get('fingerprint_stability', 0),
        })

        return jsonify({
            'message': 'License activated successfully',
            'encrypted_license': encrypted_response,
            'fingerprint_short': data.get('fingerprint_short', machine_fingerprint[:16]),
            'status': 'encrypted'
        }), 201

    except Exception as e:
        logger.error(f"Activation error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Activation failed'}), 500


# =========================
# Verify License by ID
# =========================
@bp.route('/verify/<license_id>', methods=['GET'])
def verify_license(license_id):
    try:
        license_obj = License.query.filter_by(license_id=license_id).first()

        if not license_obj:
            return jsonify({'valid': False, 'error': 'License not found'}), 404

        now = datetime.utcnow()
        is_valid = license_obj.is_active and license_obj.expiry_date > now
        days_remaining = max((license_obj.expiry_date - now).days, 0)

        return jsonify({
            'valid': is_valid,
            'license_id': license_obj.license_id,
            'plan_name': license_obj.plan_name,
            'plan_type': license_obj.plan_type,
            'activated_at': license_obj.activated_at.isoformat(),
            'expiry_date': license_obj.expiry_date.isoformat(),
            'is_active': license_obj.is_active,
            'days_remaining': days_remaining,
            'expired': not is_valid
        }), 200

    except Exception:
        return jsonify({'error': 'Verification failed'}), 500


# =========================
# Get User License
# =========================
@bp.route('/user/<user_id>', methods=['GET'])
def get_user_license(user_id):
    try:
        machine_fingerprint = request.args.get('machine_fingerprint')
        mac_address = request.args.get('mac_address')

        if machine_fingerprint:
            license_obj = License.query.filter_by(
                machine_fingerprint=machine_fingerprint,
                is_active=True
            ).first()
        elif mac_address:
            license_obj = License.query.filter_by(
                mac_address=mac_address,
                is_active=True
            ).first()
        else:
            return jsonify({'error': 'machine_fingerprint or mac_address required'}), 400

        if not license_obj:
            return jsonify({'license': None, 'has_active': False}), 200

        now = datetime.utcnow()
        is_valid = license_obj.expiry_date > now

        return jsonify({
            'license': license_obj.to_dict(),
            'has_active': is_valid,
            'days_remaining': max((license_obj.expiry_date - now).days, 0),
            'expired': not is_valid
        }), 200

    except Exception:
        return jsonify({'error': 'Failed'}), 500


# =========================
# Get License by Fingerprint
# =========================
@bp.route('/machine/fingerprint/<machine_fingerprint>', methods=['GET'])
def get_machine_license_by_fingerprint(machine_fingerprint):
    try:
        if len(machine_fingerprint) != 64:
            return jsonify({'error': 'Invalid fingerprint'}), 400

        license_obj = License.query.filter_by(
            machine_fingerprint=machine_fingerprint,
            is_active=True
        ).first()

        if not license_obj:
            return jsonify({'license': None, 'has_active': False}), 200

        now = datetime.utcnow()
        is_valid = license_obj.expiry_date > now

        license_obj.last_verified_fingerprint = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'license': license_obj.to_dict(),
            'has_active': is_valid,
            'days_remaining': max((license_obj.expiry_date - now).days, 0),
            'expired': not is_valid,
            'fingerprint_short': license_obj.fingerprint_short,
            'fingerprint_stability': license_obj.fingerprint_stability
        }), 200

    except Exception:
        return jsonify({'error': 'Failed'}), 500


# =========================
# Get License by MAC (deprecated)
# =========================
@bp.route('/machine/<mac_address>', methods=['GET'])
def get_machine_license(mac_address):
    try:
        license_obj = License.query.filter_by(
            mac_address=mac_address,
            is_active=True
        ).first()

        if not license_obj:
            return jsonify({
                'license': None,
                'has_active': False,
                'warning': 'MAC is unstable. Use fingerprint.'
            }), 200

        now = datetime.utcnow()
        is_valid = license_obj.expiry_date > now

        return jsonify({
            'license': license_obj.to_dict(),
            'has_active': is_valid,
            'days_remaining': max((license_obj.expiry_date - now).days, 0),
            'expired': not is_valid
        }), 200

    except Exception:
        return jsonify({'error': 'Failed'}), 500


# =========================
# Deactivate License
# =========================
@bp.route('/<license_id>', methods=['DELETE'])
def deactivate_license(license_id):
    try:
        lic = License.query.filter_by(license_id=license_id).first()

        if not lic:
            return jsonify({'error': 'License not found'}), 404

        lic.is_active = False
        db.session.commit()

        return jsonify({'message': 'License deactivated successfully'}), 200

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Deactivation failed'}), 500
