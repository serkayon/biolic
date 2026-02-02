"""
Encryption/Decryption utility for license data (Server version)
Uses AES-256 encryption with Fernet (symmetric encryption)
Same key derivation as desktop backend to ensure compatibility
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
import os

class LicenseEncryption:
    """Handles encryption and decryption of license data"""
    
    # Fixed salt (must match desktop)
    SALT = b'biolic_license_system_salt_v1'
    
    # Master password loaded from ENV (NOT hardcoded)
    MASTER_PASSWORD = os.getenv("LICENSE_MASTER_KEY")
    
    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        if not password:
            raise Exception("LICENSE_MASTER_KEY not set in environment")
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @classmethod
    def encrypt_license_data(cls, license_data: dict) -> str:
        try:
            json_data = json.dumps(license_data)
            key = cls._derive_key(cls.MASTER_PASSWORD, cls.SALT)
            cipher = Fernet(key)
            encrypted_data = cipher.encrypt(json_data.encode())
            return encrypted_data.decode('utf-8')
        except Exception as e:
            raise Exception("Encryption failed")
    
    @classmethod
    def decrypt_license_data(cls, encrypted_data: str) -> dict:
        try:
            key = cls._derive_key(cls.MASTER_PASSWORD, cls.SALT)
            cipher = Fernet(key)
            decrypted_data = cipher.decrypt(encrypted_data.encode())
            license_data = json.loads(decrypted_data.decode('utf-8'))
            return license_data
        except Exception:
            raise Exception("Decryption failed")
