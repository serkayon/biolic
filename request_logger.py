import logging
from flask import request, g
from datetime import datetime
import time

logger = logging.getLogger("api_logger")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

SENSITIVE_HEADERS = {"authorization", "cookie"}
SENSITIVE_PATHS = {"/api/auth/login", "/api/auth/register", "/api/otp/send-otp", "/api/otp/verify-otp"}

def setup_request_logging(app):
    """Safe request/response logging for production"""
    
    @app.before_request
    def log_request():
        g.start_time = time.time()
        
        method = request.method
        path = request.path
        remote_addr = request.remote_addr
        
        headers = {}
        for k, v in request.headers.items():
            if k.lower() in SENSITIVE_HEADERS:
                headers[k] = "***MASKED***"
            else:
                headers[k] = v
        
        logger.info(
            f"IN {method} {path} from {remote_addr} headers={headers}"
        )
    
    @app.after_request
    def log_response(response):
        duration = time.time() - g.start_time
        
        method = request.method
        path = request.path
        status_code = response.status_code
        
        logger.info(
            f"OUT {method} {path} status={status_code} duration={duration:.3f}s"
        )
        
        return response
