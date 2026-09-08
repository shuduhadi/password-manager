import pytest
import sqlite3
import db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_vault.db")


def test_init_db_creates_tables(db_path):
    """init_db should create meta and entries tables."""
    db.init_db(db_path)

    conn = sqlite3.connect(db_path)
    tables = {
        row[0] for row in
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    conn.close()

    assert "meta" in tables
    assert "entries" in tables


def test_init_db_is_idempotent(db_path):
    """Calling init_db multiple times should not error or duplicate data."""
    db.init_db(db_path)
    db.init_db(db_path)
    db.init_db(db_path)

    meta = db.get_meta(db_path)
    assert meta == {"salt": "", "hash": ""}


def test_get_meta_default_empty(db_path):
    """A freshly initialized db should have empty salt/hash."""
    meta = db.get_meta(db_path)
    assert meta["salt"] == ""
    assert meta["hash"] == ""


def test_set_meta_persists(db_path):
    """Setting meta should persist across separate calls."""
    db.set_meta("somesalt", "somehash", db_path)

    meta = db.get_meta(db_path)
    assert meta["salt"] == "somesalt"
    assert meta["hash"] == "somehash"


def test_set_meta_overwrites(db_path):
    """Setting meta twice should overwrite, not create a second row."""
    db.set_meta("salt1", "hash1", db_path)
    db.set_meta("salt2", "hash2", db_path)

    meta = db.get_meta(db_path)
    assert meta["salt"] == "salt2"
    assert meta["hash"] == "hash2"

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM meta").fetchone()[0]
    conn.close()
    assert count == 1


def test_get_entries_raw_empty(db_path):
    """A freshly initialized db should have no entries."""
    entries = db.get_entries_raw(db_path)
    assert entries == []


def test_replace_entries_stores_data(db_path):
    """replace_entries should store entries retrievable via get_entries_raw."""
    entries = [
        {"id": "id-1", "site": "gmail", "username": "user@x.com", "password": "encrypted1"},
        {"id": "id-2", "site": "github", "username": "dev@x.com", "password": "encrypted2"},
    ]
    db.replace_entries(entries, db_path)

    stored = db.get_entries_raw(db_path)
    assert len(stored) == 2
    sites = {e["site"] for e in stored}
    assert sites == {"gmail", "github"}


def test_replace_entries_fills_missing_created_at(db_path):
    """Entries without created_at should get one filled in automatically."""
    entries = [{"id": "id-1", "site": "site1", "username": "user1", "password": "enc1"}]
    db.replace_entries(entries, db_path)

    stored = db.get_entries_raw(db_path)
    assert stored[0]["created_at"]  # non-empty


def test_replace_entries_preserves_existing_created_at(db_path):
    """Entries that already have created_at should keep it, not get a new one."""
    entries = [{
        "id": "id-1", "site": "site1", "username": "user1",
        "password": "enc1", "created_at": "2020-01-01T00:00:00+00:00",
    }]
    db.replace_entries(entries, db_path)

    stored = db.get_entries_raw(db_path)
    assert stored[0]["created_at"] == "2020-01-01T00:00:00+00:00"


def test_replace_entries_is_a_full_overwrite(db_path):
    """Calling replace_entries again should replace, not append."""
    db.replace_entries(
        [{"id": "id-1", "site": "old", "username": "u", "password": "p"}], db_path
    )
    db.replace_entries(
        [{"id": "id-2", "site": "new", "username": "u2", "password": "p2"}], db_path
    )

    stored = db.get_entries_raw(db_path)
    assert len(stored) == 1
    assert stored[0]["site"] == "new"


def test_replace_entries_empty_list_clears_table(db_path):
    """Passing an empty list should clear all entries."""
    db.replace_entries(
        [{"id": "id-1", "site": "site1", "username": "u", "password": "p"}], db_path
    )
    db.replace_entries([], db_path)

    stored = db.get_entries_raw(db_path)
    assert stored == []


def test_entries_ordered_by_created_at(db_path):
    """get_entries_raw should return entries ordered by creation time."""
    entries = [
        {"id": "id-1", "site": "third", "username": "u", "password": "p", "created_at": "2020-03-01T00:00:00+00:00"},
        {"id": "id-2", "site": "first", "username": "u", "password": "p", "created_at": "2020-01-01T00:00:00+00:00"},
        {"id": "id-3", "site": "second", "username": "u", "password": "p", "created_at": "2020-02-01T00:00:00+00:00"},
    ]
    db.replace_entries(entries, db_path)

    stored = db.get_entries_raw(db_path)
    sites_in_order = [e["site"] for e in stored]
    assert sites_in_order == ["first", "second", "third"]