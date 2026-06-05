import bcrypt

def hash_master_password(password:str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

def verify_master_password(password:str, stored_hash:bytes) -> bool:
    return bcrypt.checkpw(password.encode(), stored_hash)

def generate_salt() -> bytes:
    raise NotImplementedError("Salt generation not implemented yet")

def derive_key(password:str, salt: bytes) -> bytes:
    raise NotImplementedError("Key derivation not implemented yet")