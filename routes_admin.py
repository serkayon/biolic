from flask import Blueprint, render_template, request, jsonify
from models import db, User, Machine, License, MachineLogin
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('admin', __name__, url_prefix='/admin')

# =========================
# Dashboard
# =========================
@bp.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        total_users = User.query.count()
        total_machines = MachineLogin.query.count()
        total_licenses = License.query.filter_by(is_active=True).count()
        
        return render_template(
            'admin_dashboard_main.html',
            total_users=total_users,
            total_machines=total_machines,
            total_licenses=total_licenses
        )
    
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return render_template('error.html', message="Server error"), 500

# =========================
# Users list page
# =========================
@bp.route('/users', methods=['GET'])
def users_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        users_paginated = User.query.paginate(page=page, per_page=per_page)
        
        users_with_info = []
        for user in users_paginated.items:
            machine_login = MachineLogin.query.filter_by(user_id=user.id).first()
            license = None
            if machine_login and machine_login.machine_fingerprint:
                license = License.query.filter_by(
                    machine_fingerprint=machine_login.machine_fingerprint,
                    is_active=True
                ).first()
            
            users_with_info.append({
                'user': user,
                'machine_login': machine_login,
                'license': license
            })
        
        return render_template(
            'admin_users_list.html',
            users=users_with_info,
            total=users_paginated.total,
            pages=users_paginated.pages,
            current_page=page,
            per_page=per_page,
        )
    
    except Exception as e:
        logger.error(f"Admin users error: {e}")
        return render_template('error.html', message="Server error"), 500

# =========================
# Systems list page
# =========================
@bp.route('/systems', methods=['GET'])
def systems_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        machines_paginated = MachineLogin.query.paginate(page=page, per_page=per_page)
        
        machines_with_info = []
        for login in machines_paginated.items:
            license = None
            if login.machine_fingerprint:
                license = License.query.filter_by(
                    machine_fingerprint=login.machine_fingerprint,
                    is_active=True
                ).first()
            user = User.query.get(login.user_id)
            
            machines_with_info.append({
                'machine_login': login,
                'license': license,
                'user': user
            })
        
        return render_template(
            'admin_systems_list.html',
            machines=machines_with_info,
            total=machines_paginated.total,
            pages=machines_paginated.pages,
            current_page=page,
            per_page=per_page,
        )
    
    except Exception as e:
        logger.error(f"Admin systems error: {e}")
        return render_template('error.html', message="Server error"), 500

# =========================
# Admin APIs
# =========================
@bp.route('/users/api', methods=['GET'])
def get_users_api():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)
        
        query = User.query
        if search:
            query = query.filter(
                (User.name.ilike(f'%{search}%')) |
                (User.email.ilike(f'%{search}%'))
            )
        
        users_paginated = query.paginate(page=page, per_page=per_page)
        
        users_data = []
        for user in users_paginated.items:
            machine_login = MachineLogin.query.filter_by(user_id=user.id).first()
            license = None
            if machine_login and machine_login.machine_fingerprint:
                license = License.query.filter_by(
                    machine_fingerprint=machine_login.machine_fingerprint,
                    is_active=True
                ).first()
            
            users_data.append({
                'user': user.to_dict(),
                'machine_login': machine_login.to_dict() if machine_login else None,
                'license': license.to_dict() if license else None
            })
        
        return jsonify({
            'users': users_data,
            'total': users_paginated.total,
            'pages': users_paginated.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        logger.error(f"Admin users api error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/machines/api', methods=['GET'])
def get_machines_api():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)
        
        query = MachineLogin.query
        if search:
            query = query.filter(
                (MachineLogin.machine_name.ilike(f'%{search}%')) |
                (MachineLogin.machine_id.ilike(f'%{search}%')) |
                (MachineLogin.current_email.ilike(f'%{search}%'))
            )
        
        machines_paginated = query.paginate(page=page, per_page=per_page)
        
        machines_data = []
        for login in machines_paginated.items:
            license = None
            if login.machine_fingerprint:
                license = License.query.filter_by(
                    machine_fingerprint=login.machine_fingerprint,
                    is_active=True
                ).first()
            
            machines_data.append({
                'machine_login': login.to_dict(),
                'license': license.to_dict() if license else None
            })
        
        return jsonify({
            'machines': machines_data,
            'total': machines_paginated.total,
            'pages': machines_paginated.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        logger.error(f"Admin machines api error: {e}")
        return jsonify({'error': 'Server error'}), 500
