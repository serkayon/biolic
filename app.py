import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from models import db
import routes_auth
import routes_users
import routes_machines
import routes_admin
import routes_subscriptions
import routes_otp
import email_worker 
from request_logger import setup_request_logging

def create_app(config_name='production'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    # Secure CORS
    CORS(
        app,
        origins=app.config.get("CORS_ORIGINS", ["*"]),
        supports_credentials=True
    )
    
    # Setup logging
    setup_request_logging(app)
    
    # Create tables (dev only)
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    app.register_blueprint(routes_auth.bp)
    app.register_blueprint(routes_users.bp)
    app.register_blueprint(routes_machines.bp)
    app.register_blueprint(routes_admin.bp)
    app.register_blueprint(routes_subscriptions.bp)
    app.register_blueprint(routes_otp.bp)
    
    # Health check
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    # Home
    @app.route('/')
    def index():
        return jsonify({"service": "Bio Radar API", "status": "running"})
    
    return app

# 🔥 REQUIRED FOR RENDER
app = create_app()

# Local only
if __name__ == '__main__':
    env = os.getenv("FLASK_ENV", "development")
    app.run(host='0.0.0.0', port=5000, debug=True)

