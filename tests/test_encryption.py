import pytest
import bcrypt
from encryption import hash_master_password, verify_master_password, generate_salt, derive_key

def test_hash_returns_bytes():
    result = hash_master_password("mypassword")
    assert isinstance(result, bytes)

def test_hash_looks_like_bcrypt():
    result = hash_master_password("mypassword")
    assert result.startswith(b"$2b$12$")

def test_verify_correct_password():
    stored = hash_master_password("mypassword")
    assert verify_master_password("mypassword", stored) is True

def test_verify_incorrect_password():
    stored = hash_master_password("maypassword")
    assert verify_master_password("wrongpassword", stored) is False

def test_hash_different_each_time():
    hash1 = hash_master_password("mypassword")
    hash2 = hash_master_password("mypassword")
    assert hash1 != hash2

def test_generate_salt_returns_bytes():
    salt = generate_salt()
    assert isinstance(salt,bytes)

def test_generate_salt_length():
    salt = generate_salt()
    assert len(salt) == 16

def test_same_password_same_salt_same_key():
    salt = generate_salt()

    key1 = derive_key("mypassword", salt)
    key2 = derive_key("mypassword", salt)
    assert key1 == key2

def test_diff_salts_diff_keys():
    salt1 = generate_salt()
    salt2 = generate_salt()

    key1 = derive_key("mypassword", salt1)
    key2 = derive_key("mypassword", salt2)
    assert key1 != key2

def test_key_is_44_characters():
    salt = generate_salt()
    key = derive_key("mypassowrd", salt)
    assert len(key) == 44
