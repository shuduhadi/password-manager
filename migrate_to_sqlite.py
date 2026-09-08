"""One-time migration: import an existing vault.json into vault.db (SQLite).

Usage:
    python migrate_to_sqlite.py
    python migrate_to_sqlite.py --json vault.json --db vault.db

Safe to run even if vault.db already has data — this overwrites the
meta row and does a full re-sync of entries, same as save_vault().
"""
import argparse
import json
from pathlib import Path

import db


def migrate(json_path: str = "vault.json", db_path: str = "vault.db") -> int:
    """Read vault.json and write its contents into the SQLite database.

    Args:
        json_path: Path to the existing vault.json file.
        db_path: Path to the SQLite database to write to.

    Returns:
        The number of entries migrated.

    Raises:
        FileNotFoundError: If json_path doesn't exist.
    """
    json_file = Path(json_path)
    if not json_file.exists():
        raise FileNotFoundError(f"{json_path} not found — nothing to migrate")

    content = json_file.read_text().strip()
    old_vault = json.loads(content) if content else {"salt": "", "hash": "", "entries": []}

    db.init_db(db_path)
    db.set_meta(old_vault.get("salt", ""), old_vault.get("hash", ""), db_path)

    entries = old_vault.get("entries", [])
    # Old JSON entries may not have created_at — replace_entries fills
    # one in automatically for any entry missing it.
    db.replace_entries(entries, db_path)

    return len(entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate vault.json to vault.db (SQLite)")
    parser.add_argument("--json", default="vault.json", help="Path to existing vault.json (default: vault.json)")
    parser.add_argument("--db", default="vault.db", help="Path to write the new SQLite database (default: vault.db)")
    args = parser.parse_args()

    try:
        count = migrate(args.json, args.db)
    except FileNotFoundError as exc:
        print(f"✗ {exc}")
        raise SystemExit(1)

    plural = "y" if count == 1 else "ies"
    print(f"✓ Migrated {count} entr{plural} from {args.json} to {args.db}")
    print(f"  You can now delete {args.json} once you've confirmed {args.db} works — it's no longer read by the app.")