import pytest
import sys
from pathlib import Path
from unittest.mock import patch
from encryption import generate_salt, derive_key, hash_master_password
from vault import load_vault, save_vault, add_entry, get_entries
from cryptography.fernet import InvalidToken
import main


def test_first_run_creates_master_password(tmp_path, monkeypatch):
    """First run should create vault with master password."""
    vault_path = tmp_path / "vault.json"
    master_pw = "correct-horse-battery-staple"
    
    def mock_getpass(prompt=""):
        if "Enter master password" in prompt:
            return master_pw
        elif "Confirm master password" in prompt:
            return master_pw
        return ""
    
    def mock_input(prompt=""):
        return "4"  # Quit
    
    monkeypatch.setattr("getpass.getpass", mock_getpass)
    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr("main.VAULT_PATH", str(vault_path))
    
    with pytest.raises(SystemExit) as exc:
        main.main()
    assert exc.value.code == 0
    
    vault = load_vault(str(vault_path))
    assert vault["hash"]
    assert vault["salt"]


def test_unlock_existing_vault_correct_password(tmp_path, monkeypatch):
    """Unlocking with correct password should work."""
    vault_path = tmp_path / "vault.json"
    master_pw = "correct-horse-battery-staple"
    
    # Create existing vault
    salt = generate_salt()
    key = derive_key(master_pw, salt)
    pw_hash = hash_master_password(master_pw)
    vault = {
        "salt": salt.hex(),
        "hash": pw_hash.decode(),
        "entries": []
    }
    vault = add_entry(vault, "github", "user@x.com", "testpass", key)
    save_vault(vault, str(vault_path))
    
    def mock_getpass(prompt=""):
        return master_pw
    
    def mock_input(prompt=""):
        return "4"  # Quit
    
    monkeypatch.setattr("getpass.getpass", mock_getpass)
    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr("main.VAULT_PATH", str(vault_path))
    
    with pytest.raises(SystemExit) as exc:
        main.main()
    assert exc.value.code == 0


def test_unlock_existing_vault_wrong_password(tmp_path, monkeypatch):
    """Wrong password should fail after 3 attempts."""
    vault_path = tmp_path / "vault.json"
    master_pw = "correct-horse-battery-staple"
    
    # Create existing vault
    salt = generate_salt()
    key = derive_key(master_pw, salt)
    pw_hash = hash_master_password(master_pw)
    vault = {
        "salt": salt.hex(),
        "hash": pw_hash.decode(),
        "entries": []
    }
    save_vault(vault, str(vault_path))
    
    def mock_getpass(prompt=""):
        return "wrong-password"
    
    monkeypatch.setattr("getpass.getpass", mock_getpass)
    monkeypatch.setattr("main.VAULT_PATH", str(vault_path))
    
    with pytest.raises(SystemExit) as exc:
        main.main()
    assert exc.value.code == 0


def test_add_password_flow(tmp_path, monkeypatch):
    """Adding a password through menu should save it."""
    vault_path = tmp_path / "vault.json"
    master_pw = "master-password"
    
    # Create vault
    salt = generate_salt()
    key = derive_key(master_pw, salt)
    pw_hash = hash_master_password(master_pw)
    vault = {
        "salt": salt.hex(),
        "hash": pw_hash.decode(),
        "entries": []
    }
    save_vault(vault, str(vault_path))
    
    getpass_calls = iter([master_pw, "newpassword"])
    
    def mock_getpass(prompt=""):
        return next(getpass_calls, "")
    
    input_calls = iter(["1", "github", "dev@x.com", "4"])
    
    def mock_input(prompt=""):
        return next(input_calls, "4")
    
    monkeypatch.setattr("getpass.getpass", mock_getpass)
    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr("main.VAULT_PATH", str(vault_path))
    
    with pytest.raises(SystemExit):
        main.main()
    
    # Verify password was saved
    reloaded = load_vault(str(vault_path))
    assert len(reloaded["entries"]) == 1
    assert reloaded["entries"][0]["site"] == "github"


def test_add_password_missing_fields(tmp_path, monkeypatch):
    """Adding password with missing fields should reject."""
    vault_path = tmp_path / "vault.json"
    master_pw = "master-password"
    
    # Create vault
    salt = generate_salt()
    key = derive_key(master_pw, salt)
    pw_hash = hash_master_password(master_pw)
    vault = {
        "salt": salt.hex(),
        "hash": pw_hash.decode(),
        "entries": []
    }
    save_vault(vault, str(vault_path))
    
    getpass_calls = iter([master_pw, ""])  # Empty password
    
    def mock_getpass(prompt=""):
        return next(getpass_calls, "")
    
    input_calls = iter(["1", "github", "", "4"])  # Empty username
    
    def mock_input(prompt=""):
        return next(input_calls, "4")
    
    monkeypatch.setattr("getpass.getpass", mock_getpass)
    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr("main.VAULT_PATH", str(vault_path))
    
    with pytest.raises(SystemExit):
        main.main()
    
    # Verify nothing was saved
    reloaded = load_vault(str(vault_path))
    assert len(reloaded["entries"]) == 0


def test_delete_password_flow(tmp_path, monkeypatch):
    """Deleting a password should remove it."""
    vault_path = tmp_path / "vault.json"
    master_pw = "master-password"
    
    # Create vault with entry
    salt = generate_salt()
    key = derive_key(master_pw, salt)
    pw_hash = hash_master_password(master_pw)
    vault = {
        "salt": salt.hex(),
        "hash": pw_hash.decode(),
        "entries": []
    }
    vault = add_entry(vault, "github", "dev@x.com", "ghpass", key)
    save_vault(vault, str(vault_path))
    
    def mock_getpass(prompt=""):
        return master_pw
    
    input_calls = iter(["3", "1", "4"])  # Delete menu, choice 1, quit
    
    def mock_input(prompt=""):
        return next(input_calls, "4")
    
    monkeypatch.setattr("getpass.getpass", mock_getpass)
    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr("main.VAULT_PATH", str(vault_path))
    
    with pytest.raises(SystemExit):
        main.main()
    
    # Verify entry was deleted
    reloaded = load_vault(str(vault_path))
    assert len(reloaded["entries"]) == 0


def test_delete_password_cancel(tmp_path, monkeypatch):
    """Choosing 0 in delete should cancel."""
    vault_path = tmp_path / "vault.json"
    master_pw = "master-password"
    
    # Create vault with entry
    salt = generate_salt()
    key = derive_key(master_pw, salt)
    pw_hash = hash_master_password(master_pw)
    vault = {
        "salt": salt.hex(),
        "hash": pw_hash.decode(),
        "entries": []
    }
    vault = add_entry(vault, "github", "dev@x.com", "ghpass", key)
    save_vault(vault, str(vault_path))
    
    def mock_getpass(prompt=""):
        return master_pw
    
    input_calls = iter(["3", "0", "4"])  # Delete menu, cancel (0), quit
    
    def mock_input(prompt=""):
        return next(input_calls, "4")
    
    monkeypatch.setattr("getpass.getpass", mock_getpass)
    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr("main.VAULT_PATH", str(vault_path))
    
    with pytest.raises(SystemExit):
        main.main()
    
    # Verify entry is still there
    reloaded = load_vault(str(vault_path))
    assert len(reloaded["entries"]) == 1