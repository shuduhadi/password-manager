import pytest
import bcrypt
from encryption import hash_master_password, verify_master_password

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