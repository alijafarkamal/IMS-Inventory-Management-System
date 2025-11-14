"""Cryptography utilities for field-level encryption."""
from cryptography.fernet import Fernet
from inventory_app.config import ENCRYPTION_KEY_LENGTH
from inventory_app.utils.logging import logger
import base64
import os
from pathlib import Path

# Key file path
KEY_FILE = Path(__file__).parent.parent.parent.parent / "data" / ".encryption_key"


def get_or_create_key() -> bytes:
    """Get or create encryption key."""
    if KEY_FILE.exists():
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        KEY_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        # Set restrictive permissions
        os.chmod(KEY_FILE, 0o600)
        logger.info("Generated new encryption key")
        return key


def encrypt_field(value: str) -> str:
    """Encrypt a sensitive field value."""
    if not value:
        return value
    try:
        key = get_or_create_key()
        f = Fernet(key)
        encrypted = f.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return value


def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a sensitive field value."""
    if not encrypted_value:
        return encrypted_value
    try:
        key = get_or_create_key()
        f = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = f.decrypt(decoded)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return encrypted_value

