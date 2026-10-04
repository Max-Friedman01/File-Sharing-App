import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets

def hash_password(password: str) -> str:
    ph = PasswordHasher()
    return ph.hash(password)

def verify_password(stored: str, password: str) -> bool:
    ph = PasswordHasher()
    try:
        ph.verify(stored, password)
    except VerifyMismatchError:
        return False
    else:
        return True

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def generate_manager_token() -> str:
    return secrets.token_urlsafe(32)

def generate_share_code() -> str:
     return secrets.token_urlsafe(16)

def generate_stored_name() -> str:
     return secrets.token_hex(16)