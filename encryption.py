import bcrypt
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken

def hash_master_password(password:str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

def verify_master_password(password:str, stored_hash:bytes) -> bool:
    return bcrypt.checkpw(password.encode(), stored_hash)

def generate_salt() -> bytes:
    return os.urandom(16)

def derive_key(password:str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC (
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(key)

def encrypt_password(plaintext: str, key: bytes) -> str:
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plaintext.encode())
    return encrypted.decode()

def decrypt_password(token: str, key:bytes) -> str:
    fernet = Fernet(key)
    decrypted = fernet.decrypt(token.encode())
    return decrypted.decode()