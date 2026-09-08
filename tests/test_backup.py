import json
import pytest

from encryption import generate_salt, derive_key, hash_master_password
from vault import add_entry, get_entries
from backup import export_backup, import_backup, merge_entries, BackupPasswordError, BackupFormatError


MASTER_PASSWORD = "correct-horse-battery-staple"
OTHER_PASSWORD = "wrong-horse-battery-staple"


def _make_vault(password=MASTER_PASSWORD):
    """Build a fresh in-memory vault dict + its Fernet key, matching how
    LoginWindow / vault.py set things up (no disk I/O)."""
    salt = generate_salt()
    key = derive_key(password, salt)
    pw_hash = hash_master_password(password)
    vault = {"salt": salt.hex(), "hash": pw_hash.decode(), "entries": []}
    return vault, key


def test_export_creates_file(tmp_path):
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)

    out_path = tmp_path / "backup.vaultbak"
    export_backup(vault, key, str(out_path))

    assert out_path.exists()


def test_export_returns_entry_count(tmp_path):
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)
    vault = add_entry(vault, "github", "dev@x.com", "ghpass", key)

    out_path = tmp_path / "backup.vaultbak"
    count = export_backup(vault, key, str(out_path))

    assert count == 2


def test_export_file_has_no_plaintext_leakage(tmp_path):
    """Site, username, and password should not appear anywhere in the raw file."""
    vault, key = _make_vault()
    vault = add_entry(vault, "supersecretsite", "myusername123", "mypassword456", key)

    out_path = tmp_path / "backup.vaultbak"
    export_backup(vault, key, str(out_path))

    raw = out_path.read_text()
    assert "supersecretsite" not in raw
    assert "myusername123" not in raw
    assert "mypassword456" not in raw


def test_export_file_is_valid_json_with_expected_shape(tmp_path):
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)

    out_path = tmp_path / "backup.vaultbak"
    export_backup(vault, key, str(out_path))

    with open(out_path) as f:
        parsed = json.load(f)

    assert parsed["format"] == "pyvault-backup"
    assert "salt" in parsed
    assert "data" in parsed


def test_import_correct_password_returns_entries(tmp_path):
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)
    vault = add_entry(vault, "github", "dev@x.com", "ghpass", key)

    out_path = tmp_path / "backup.vaultbak"
    export_backup(vault, key, str(out_path))

    entries = import_backup(str(out_path), MASTER_PASSWORD)

    assert len(entries) == 2
    sites = {e["site"] for e in entries}
    assert sites == {"gmail", "github"}


def test_import_wrong_password_raises(tmp_path):
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)

    out_path = tmp_path / "backup.vaultbak"
    export_backup(vault, key, str(out_path))

    with pytest.raises(BackupPasswordError):
        import_backup(str(out_path), OTHER_PASSWORD)


def test_import_nonexistent_file_raises_format_error(tmp_path):
    missing_path = tmp_path / "does-not-exist.vaultbak"

    with pytest.raises(BackupFormatError):
        import_backup(str(missing_path), MASTER_PASSWORD)


def test_import_invalid_json_raises_format_error(tmp_path):
    bad_path = tmp_path / "bad.vaultbak"
    bad_path.write_text("this is not json {{{")

    with pytest.raises(BackupFormatError):
        import_backup(str(bad_path), MASTER_PASSWORD)


def test_import_missing_format_field_raises_format_error(tmp_path):
    bad_path = tmp_path / "bad.vaultbak"
    bad_path.write_text(json.dumps({"salt": "abcd", "data": "xyz"}))

    with pytest.raises(BackupFormatError):
        import_backup(str(bad_path), MASTER_PASSWORD)


def test_import_wrong_file_format_raises_format_error(tmp_path):
    """A random JSON file that isn't a PyVault backup at all."""
    bad_path = tmp_path / "random.json"
    bad_path.write_text(json.dumps({"hello": "world"}))

    with pytest.raises(BackupFormatError):
        import_backup(str(bad_path), MASTER_PASSWORD)


def test_roundtrip_preserves_all_data(tmp_path):
    """Export then import should recover the exact same site/username/password data."""
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)
    vault = add_entry(vault, "github", "dev@x.com", "ghpass!@#$", key)
    vault = add_entry(vault, "twitter", "handle", "birdword123", key)

    out_path = tmp_path / "backup.vaultbak"
    export_backup(vault, key, str(out_path))

    imported = import_backup(str(out_path), MASTER_PASSWORD)

    original = {(e["site"], e["username"]): e["password"] for e in get_entries(vault, key)}
    recovered = {(e["site"], e["username"]): e["password"] for e in imported}

    assert original == recovered


def test_merge_adds_new_entries():
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)

    imported = [{"site": "github", "username": "dev@x.com", "password": "ghpass"}]

    vault, added, skipped = merge_entries(vault, key, imported)

    assert added == 1
    assert skipped == 0
    sites = {e["site"] for e in get_entries(vault, key)}
    assert sites == {"gmail", "github"}


def test_merge_skips_exact_duplicates():
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)

    imported = [{"site": "gmail", "username": "user@x.com", "password": "differentpass"}]

    vault, added, skipped = merge_entries(vault, key, imported)

    assert added == 0
    assert skipped == 1
    entries = get_entries(vault, key)
    assert len(entries) == 1
    # Original password should be untouched — merge does not overwrite existing entries
    assert entries[0]["password"] == "gmailpass"


def test_merge_dedup_is_case_insensitive_and_trims_whitespace():
    vault, key = _make_vault()
    vault = add_entry(vault, "Gmail", "User@X.com", "gmailpass", key)

    imported = [{"site": "  gmail ", "username": " user@x.com ", "password": "otherpass"}]

    vault, added, skipped = merge_entries(vault, key, imported)

    assert added == 0
    assert skipped == 1


def test_merge_dedups_within_the_import_file_itself():
    """Two identical entries in one import file should only be added once."""
    vault, key = _make_vault()

    imported = [
        {"site": "newsite", "username": "user", "password": "pass1"},
        {"site": "newsite", "username": "user", "password": "pass2"},
    ]

    vault, added, skipped = merge_entries(vault, key, imported)

    assert added == 1
    assert skipped == 1
    entries = get_entries(vault, key)
    assert len(entries) == 1


def test_merge_returns_updated_vault_with_correct_total():
    vault, key = _make_vault()
    vault = add_entry(vault, "gmail", "user@x.com", "gmailpass", key)

    imported = [
        {"site": "github", "username": "dev@x.com", "password": "ghpass"},
        {"site": "twitter", "username": "handle", "password": "birdpass"},
    ]

    vault, added, skipped = merge_entries(vault, key, imported)

    assert added == 2
    assert skipped == 0
    assert len(vault["entries"]) == 3