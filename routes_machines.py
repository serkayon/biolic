from flask import Blueprint, request, jsonify
from models import db, User, Machine
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('machines', __name__, url_prefix='/api/machines')

# =========================
# Get all machines for user
# =========================
@bp.route('', methods=['GET'])
def get_machines():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        machines = Machine.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'machines': [machine.to_dict() for machine in machines]
        }), 200
    
    except Exception as e:
        logger.error(f"Get machines error: {e}")
        return jsonify({'error': 'Failed to fetch machines'}), 500

# =========================
# Register new machine
# =========================
@bp.route('', methods=['POST'])
def register_machine():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        required_fields = ['machine_id', 'machine_name', 'mac_address']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if machine already exists
        if Machine.query.filter_by(machine_id=data['machine_id']).first():
            return jsonify({'error': 'Machine already registered'}), 409
        
        machine = Machine(
            user_id=user_id,
            mac_address=data['mac_address'],
            machine_name=data['machine_name'],
            machine_id=data['machine_id'],
            os_name=data.get('os_name'),
            os_version=data.get('os_version'),
            processor=data.get('processor'),
        )
        
        db.session.add(machine)
        db.session.commit()
        
        return jsonify({
            'message': 'Machine registered successfully',
            'machine': machine.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Register machine error: {e}")
        return jsonify({'error': 'Machine registration failed'}), 500

# =========================
# Get single machine
# =========================
@bp.route('/<machine_id>', methods=['GET'])
def get_machine(machine_id):
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        machine = Machine.query.filter_by(
            id=machine_id,
            user_id=user_id
        ).first()
        
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        return jsonify({'machine': machine.to_dict()}), 200
    
    except Exception as e:
        logger.error(f"Get machine error: {e}")
        return jsonify({'error': 'Failed to fetch machine'}), 500

# =========================
# Update machine
# =========================
@bp.route('/<machine_id>', methods=['PUT'])
def update_machine(machine_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        machine = Machine.query.filter_by(
            id=machine_id,
            user_id=user_id
        ).first()
        
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        if 'machine_name' in data:
            machine.machine_name = data['machine_name']
        if 'is_active' in data:
            machine.is_active = data['is_active']
        
        machine.last_seen = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Machine updated successfully',
            'machine': machine.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update machine error: {e}")
        return jsonify({'error': 'Machine update failed'}), 500

# =========================
# Delete machine
# =========================
@bp.route('/<machine_id>', methods=['DELETE'])
def delete_machine(machine_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        machine = Machine.query.filter_by(
            id=machine_id,
            user_id=user_id
        ).first()
        
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        db.session.delete(machine)
        db.session.commit()
        
        return jsonify({'message': 'Machine deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete machine error: {e}")
        return jsonify({'error': 'Machine deletion failed'}), 500
