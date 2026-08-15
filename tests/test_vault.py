import pytest
import json
from cryptography.fernet import InvalidToken
from vault import load_vault, save_vault, add_entry, delete_entry, get_entries


def test_load_missing_vault_returns_empty_structure(tmp_vault):
    """Loading a non-existent vault should return empty but valid structure."""
    vault = load_vault(str(tmp_vault))
    assert vault["salt"] == ""
    assert vault["hash"] == ""
    assert vault["entries"] == []


def test_save_and_reload_vault(tmp_vault, key):
    """Vault saved and reloaded should have identical data."""
    vault = load_vault(str(tmp_vault))
    vault["salt"] = "test_salt"
    vault["hash"] = "$2b$12$test_hash"
    vault = add_entry(vault, "gmail", "user@x.com", "plaintext_pass_123", key)
    
    save_vault(vault, str(tmp_vault))
    
    reloaded = load_vault(str(tmp_vault))
    assert reloaded["salt"] == "test_salt"
    assert reloaded["hash"] == "$2b$12$test_hash"
    assert len(reloaded["entries"]) == 1
    assert reloaded["entries"][0]["site"] == "gmail"
    assert reloaded["entries"][0]["username"] == "user@x.com"
    # Password should be encrypted in storage
    assert reloaded["entries"][0]["password"].startswith("gAAAAA")


def test_add_entry_encrypts_password(tmp_vault, key):
    """Password should be encrypted when added."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "github", "dev@x.com", "my-secret-password", key)
    
    entry = vault["entries"][0]
    assert "id" in entry
    # Password in storage should be encrypted, not plaintext
    assert entry["password"] != "my-secret-password"
    assert entry["password"].startswith("gAAAAA")


def test_add_entry_creates_uuid(tmp_vault, key):
    """Each entry should get a unique UUID."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "github", "dev@x.com", "pass", key)
    
    entry = vault["entries"][0]
    assert "id" in entry
    assert len(entry["id"]) == 36  # UUID4 format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx


def test_add_entry_stores_all_fields(tmp_vault, key):
    """Entry should store site, username, and (encrypted) password."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "twitter", "handle@x.com", "secret123", key)
    
    entry = vault["entries"][0]
    assert entry["site"] == "twitter"
    assert entry["username"] == "handle@x.com"
    assert entry["password"].startswith("gAAAAA")  # Should be encrypted


def test_add_multiple_entries(tmp_vault, key):
    """Should be able to add multiple entries to same vault."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "gmail", "a@x.com", "pass1", key)
    vault = add_entry(vault, "github", "b@x.com", "pass2", key)
    vault = add_entry(vault, "twitter", "c@x.com", "pass3", key)
    
    assert len(vault["entries"]) == 3


def test_delete_entry_removes_it(tmp_vault, key):
    """Deleting an entry should remove it from vault."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "github", "dev@x.com", "pass_encrypted", key)
    entry_id = vault["entries"][0]["id"]
    
    vault = delete_entry(vault, entry_id)
    
    assert len(vault["entries"]) == 0


def test_delete_nonexistent_entry_does_nothing(tmp_vault, key):
    """Deleting a non-existent entry should not crash."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "github", "dev@x.com", "pass", key)
    
    vault = delete_entry(vault, "fake-uuid-that-doesnt-exist")
    
    assert len(vault["entries"]) == 1  # Original entry still there


def test_get_entries_decrypts_passwords(tmp_vault, key):
    """get_entries should return entries with decrypted passwords."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "gmail", "user@x.com", "my-password", key)
    vault = add_entry(vault, "github", "dev@x.com", "dev-password", key)
    
    entries = get_entries(vault, key)
    
    assert len(entries) == 2
    assert entries[0]["site"] == "gmail"
    assert entries[0]["password"] == "my-password"  # Should be decrypted
    assert entries[1]["site"] == "github"
    assert entries[1]["password"] == "dev-password"  # Should be decrypted


def test_get_entries_with_wrong_key_raises(tmp_vault, salt):
    """Decrypting with wrong key should raise InvalidToken."""
    from encryption import derive_key
    
    key1 = derive_key("password1", salt)
    key2 = derive_key("password2", salt)
    
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "site", "user", "password", key1)
    save_vault(vault, str(tmp_vault))
    
    reloaded = load_vault(str(tmp_vault))
    with pytest.raises(InvalidToken):
        get_entries(reloaded, key2)


def test_vault_file_is_valid_json(tmp_vault, key):
    """Saved vault file should be valid JSON."""
    vault = load_vault(str(tmp_vault))
    vault["salt"] = "test_salt"
    vault = add_entry(vault, "site", "user", "pass", key)
    
    save_vault(vault, str(tmp_vault))
    
    # Read raw JSON to verify it's valid
    with open(tmp_vault) as f:
        parsed = json.load(f)
    
    assert parsed["salt"] == "test_salt"
    assert len(parsed["entries"]) == 1