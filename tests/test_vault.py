import pytest
import json
from vault import load_vault, save_vault, add_entry, delete_entry, get_entries


def test_load_missing_vault_returns_empty_structure(tmp_vault):
    """Loading a non-existent vault should return empty but valid structure."""
    vault = load_vault(str(tmp_vault))
    assert vault["salt"] == ""
    assert vault["hash"] == ""
    assert vault["entries"] == []


def test_save_and_reload_vault(tmp_vault):
    """Vault saved and reloaded should have identical data."""
    vault = load_vault(str(tmp_vault))
    vault["salt"] = "test_salt"
    vault["hash"] = "$2b$12$test_hash"
    vault = add_entry(vault, "gmail", "user@x.com", "encrypted_pass_123")
    
    save_vault(vault, str(tmp_vault))
    
    reloaded = load_vault(str(tmp_vault))
    assert reloaded["salt"] == "test_salt"
    assert reloaded["hash"] == "$2b$12$test_hash"
    assert len(reloaded["entries"]) == 1
    assert reloaded["entries"][0]["site"] == "gmail"
    assert reloaded["entries"][0]["username"] == "user@x.com"
    assert reloaded["entries"][0]["password"] == "encrypted_pass_123"


def test_add_entry_creates_uuid(tmp_vault):
    """Each entry should get a unique UUID."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "github", "dev@x.com", "pass_encrypted")
    
    entry = vault["entries"][0]
    assert "id" in entry
    assert len(entry["id"]) == 36  # UUID4 format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx


def test_add_entry_stores_all_fields(tmp_vault):
    """Entry should store site, username, and encrypted password."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "twitter", "handle@x.com", "gAAAAAB...")
    
    entry = vault["entries"][0]
    assert entry["site"] == "twitter"
    assert entry["username"] == "handle@x.com"
    assert entry["password"] == "gAAAAAB..."


def test_add_multiple_entries(tmp_vault):
    """Should be able to add multiple entries to same vault."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "gmail", "a@x.com", "pass1")
    vault = add_entry(vault, "github", "b@x.com", "pass2")
    vault = add_entry(vault, "twitter", "c@x.com", "pass3")
    
    assert len(vault["entries"]) == 3


def test_delete_entry_removes_it(tmp_vault):
    """Deleting an entry should remove it from vault."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "github", "dev@x.com", "pass_encrypted")
    entry_id = vault["entries"][0]["id"]
    
    vault = delete_entry(vault, entry_id)
    
    assert len(vault["entries"]) == 0


def test_delete_nonexistent_entry_does_nothing(tmp_vault):
    """Deleting a non-existent entry should not crash."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "github", "dev@x.com", "pass")
    
    vault = delete_entry(vault, "fake-uuid-that-doesnt-exist")
    
    assert len(vault["entries"]) == 1  # Original entry still there


def test_get_entries_returns_list(tmp_vault):
    """get_entries should return the entries list."""
    vault = load_vault(str(tmp_vault))
    vault = add_entry(vault, "site1", "user1", "pass1")
    vault = add_entry(vault, "site2", "user2", "pass2")
    
    entries = get_entries(vault)
    
    assert len(entries) == 2
    assert entries[0]["site"] == "site1"
    assert entries[1]["site"] == "site2"


def test_vault_file_is_valid_json(tmp_vault):
    """Saved vault file should be valid JSON."""
    vault = load_vault(str(tmp_vault))
    vault["salt"] = "test_salt"
    vault = add_entry(vault, "site", "user", "pass")
    
    save_vault(vault, str(tmp_vault))
    
    # Read raw JSON to verify it's valid
    with open(tmp_vault) as f:
        parsed = json.load(f)
    
    assert parsed["salt"] == "test_salt"
    assert len(parsed["entries"]) == 1