import pytest
from encryption import derive_key, generate_salt

TEST_PASSWORD = "correct-horse-battery-staple"

@pytest.fixture
def salt():
    return generate_salt()

@pytest.fixture
def key(salt):
    return derive_key(TEST_PASSWORD, salt)

@pytest.fixture
def tmp_vault(tmp_path):
    return tmp_path / "vault.json"