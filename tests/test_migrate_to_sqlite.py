import pytest
import json
from migrate_to_sqlite import migrate
import db


def test_migrate_raises_if_json_missing(tmp_path):
    """Migrating a nonexistent vault.json should raise FileNotFoundError."""
    missing_json = tmp_path / "does_not_exist.json"
    db_path = tmp_path / "vault.db"

    with pytest.raises(FileNotFoundError):
        migrate(str(missing_json), str(db_path))


def test_migrate_empty_json(tmp_path):
    """Migrating an empty vault.json should produce an empty db, 0 entries."""
    json_path = tmp_path / "vault.json"
    json_path.write_text("")
    db_path = tmp_path / "vault.db"

    count = migrate(str(json_path), str(db_path))

    assert count == 0
    meta = db.get_meta(str(db_path))
    assert meta["salt"] == ""
    assert meta["hash"] == ""


def test_migrate_transfers_meta(tmp_path):
    """Migration should carry over salt and hash."""
    json_path = tmp_path / "vault.json"
    json_path.write_text(json.dumps({
        "salt": "abc123",
        "hash": "$2b$12$somehash",
        "entries": [],
    }))
    db_path = tmp_path / "vault.db"

    migrate(str(json_path), str(db_path))

    meta = db.get_meta(str(db_path))
    assert meta["salt"] == "abc123"
    assert meta["hash"] == "$2b$12$somehash"


def test_migrate_transfers_entries(tmp_path):
    """Migration should carry over every entry."""
    json_path = tmp_path / "vault.json"
    json_path.write_text(json.dumps({
        "salt": "abc123",
        "hash": "$2b$12$somehash",
        "entries": [
            {"id": "id-1", "site": "gmail", "username": "a@x.com", "password": "gAAAAA1"},
            {"id": "id-2", "site": "github", "username": "b@x.com", "password": "gAAAAA2"},
        ],
    }))
    db_path = tmp_path / "vault.db"

    count = migrate(str(json_path), str(db_path))

    assert count == 2
    entries = db.get_entries_raw(str(db_path))
    sites = {e["site"] for e in entries}
    assert sites == {"gmail", "github"}


def test_migrate_preserves_encrypted_passwords(tmp_path):
    """Migrated passwords should stay encrypted (untouched) — migration
    never has access to the master password, so it can't decrypt anything."""
    json_path = tmp_path / "vault.json"
    json_path.write_text(json.dumps({
        "salt": "abc123",
        "hash": "$2b$12$somehash",
        "entries": [
            {"id": "id-1", "site": "gmail", "username": "a@x.com", "password": "gAAAAABencryptedtoken"},
        ],
    }))
    db_path = tmp_path / "vault.db"

    migrate(str(json_path), str(db_path))

    entries = db.get_entries_raw(str(db_path))
    assert entries[0]["password"] == "gAAAAABencryptedtoken"


def test_migrate_is_rerunnable(tmp_path):
    """Running migrate twice should not duplicate entries."""
    json_path = tmp_path / "vault.json"
    json_path.write_text(json.dumps({
        "salt": "abc123",
        "hash": "$2b$12$somehash",
        "entries": [
            {"id": "id-1", "site": "gmail", "username": "a@x.com", "password": "gAAAAA1"},
        ],
    }))
    db_path = tmp_path / "vault.db"

    migrate(str(json_path), str(db_path))
    migrate(str(json_path), str(db_path))

    entries = db.get_entries_raw(str(db_path))
    assert len(entries) == 1