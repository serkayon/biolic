from flask import Blueprint, request, jsonify
from models import db, User
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('users', __name__, url_prefix='/api/users')

# =========================
# Get current user profile
# =========================
@bp.route('/profile', methods=['GET'])
def get_profile():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': user.to_dict()}), 200

    except Exception:
        return jsonify({'error': 'Failed to fetch profile'}), 500


# =========================
# Update current user profile
# =========================
@bp.route('/profile', methods=['PUT'])
def update_profile():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        if 'name' in data:
            user.name = data['name']

        db.session.commit()

        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500


# =========================
# Get any user (self only for now)
# =========================
@bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': user.to_dict()}), 200

    except Exception:
        return jsonify({'error': 'Failed to fetch user'}), 500


# =========================
# List users (ADMIN only)
# =========================
@bp.route('', methods=['GET'])
def list_users():
    try:
        admin_email = request.args.get('admin_email')
        if admin_email != "admin@serkayon.com":
            return jsonify({'error': 'Admin access required'}), 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        users = User.query.paginate(page=page, per_page=per_page)

        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page,
        }), 200

    except Exception:
        return jsonify({'error': 'Failed to list users'}), 500
