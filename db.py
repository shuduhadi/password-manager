import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


DB_PATH = "vault.db"


@contextmanager
def _connect(path: str = DB_PATH):
    """Open a SQLite connection, commit on success, always close."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path: str = DB_PATH) -> None:
    """Create the meta and entries tables if they don't already exist.

    Safe to call every time before any other operation — CREATE TABLE IF
    NOT EXISTS makes this idempotent.
    """
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                salt TEXT NOT NULL DEFAULT '',
                hash TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                site TEXT NOT NULL,
                username TEXT NOT NULL,
                password_enc TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        # Single-row meta table (id is always 1) — insert it once if missing.
        conn.execute("INSERT OR IGNORE INTO meta (id, salt, hash) VALUES (1, '', '')")


def get_meta(path: str = DB_PATH) -> dict:
    """Return the stored salt/hash, or empty strings if never set."""
    init_db(path)
    with _connect(path) as conn:
        row = conn.execute("SELECT salt, hash FROM meta WHERE id = 1").fetchone()
        if row is None:
            return {"salt": "", "hash": ""}
        return {"salt": row["salt"], "hash": row["hash"]}


def set_meta(salt: str, hash_: str, path: str = DB_PATH) -> None:
    """Overwrite the stored salt/hash."""
    init_db(path)
    with _connect(path) as conn:
        conn.execute("UPDATE meta SET salt = ?, hash = ? WHERE id = 1", (salt, hash_))


def get_entries_raw(path: str = DB_PATH) -> list[dict]:
    """Return all entries with passwords still encrypted, ordered by creation time."""
    init_db(path)
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT id, site, username, password_enc, created_at "
            "FROM entries ORDER BY created_at"
        ).fetchall()
        return [
            {
                "id": row["id"],
                "site": row["site"],
                "username": row["username"],
                "password": row["password_enc"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


def replace_entries(entries: list[dict], path: str = DB_PATH) -> None:
    """Overwrite the entries table with the given list (full re-sync).

    This matches the existing save_vault contract: saving always
    re-persists the complete in-memory entry list, not a diff.
    Entries missing created_at get one filled in now.
    """
    init_db(path)
    with _connect(path) as conn:
        conn.execute("DELETE FROM entries")
        for entry in entries:
            conn.execute(
                "INSERT INTO entries (id, site, username, password_enc, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    entry["id"],
                    entry["site"],
                    entry["username"],
                    entry["password"],
                    entry.get("created_at") or _now_iso(),
                ),
            )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()