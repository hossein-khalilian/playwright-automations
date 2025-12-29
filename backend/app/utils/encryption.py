"""
Encryption utilities for securely storing email passwords.
Uses Fernet (symmetric encryption) from the cryptography library.
"""
import base64
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.utils.config import config


def _get_encryption_key() -> bytes:
    """
    Get encryption key from environment variable.
    ENCRYPTION_KEY should be a base64-encoded Fernet key.
    Generate one using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
    """
    encryption_key_str = config.get("encryption_key")
    
    if not encryption_key_str:
        raise ValueError(
            "ENCRYPTION_KEY must be set in environment variables. "
            "Generate one using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    # Try to use it directly as a Fernet key (should be base64-encoded)
    try:
        # Validate it's a valid Fernet key by trying to create a Fernet instance
        key_bytes = encryption_key_str.encode()
        Fernet(key_bytes)  # This will raise if key is invalid
        return key_bytes
    except Exception:
        # If direct use fails, derive a key using PBKDF2 from the provided string
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'email_password_encryption_salt',  # In production, use a random salt
            iterations=100000,
        )
        derived_key = kdf.derive(encryption_key_str.encode())
        return base64.urlsafe_b64encode(derived_key)


def encrypt_password(password: str) -> str:
    """
    Encrypt a password using Fernet symmetric encryption.
    
    Args:
        password: Plain text password to encrypt
        
    Returns:
        Base64-encoded encrypted password
    """
    key = _get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt a password that was encrypted with encrypt_password.
    
    Args:
        encrypted_password: Base64-encoded encrypted password
        
    Returns:
        Plain text password
    """
    key = _get_encryption_key()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted_password.encode())
    return decrypted.decode()

