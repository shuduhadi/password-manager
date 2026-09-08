import uuid
from datetime import datetime, timezone
from cryptography.fernet import InvalidToken
from encryption import encrypt_password, decrypt_password
import db


def load_vault(path: str = "vault.db") -> dict:
    """Load vault from the SQLite database, or return an empty structure
    if this is the first run (no meta row / no entries yet).

    Args:
        path: Path to the SQLite database file.

    Returns:
        Vault dict with the same shape the app has always used:
        {
            "salt": str (hex),
            "hash": str (bcrypt hash as string),
            "entries": [
                {"id": str, "site": str, "username": str, "password": str (encrypted), "created_at": str},
                ...
            ]
        }
    """
    meta = db.get_meta(path)
    entries = db.get_entries_raw(path)
    return {"salt": meta["salt"], "hash": meta["hash"], "entries": entries}


def save_vault(vault: dict, path: str = "vault.db") -> None:
    """Persist the given vault dict to the SQLite database.

    Overwrites the stored salt/hash and does a full re-sync of the
    entries table — same "always re-persist the full vault" behavior
    the JSON-backed version had.

    Args:
        vault: Vault dict to save
        path: Path to the SQLite database file
    """
    db.set_meta(vault.get("salt", ""), vault.get("hash", ""), path)
    db.replace_entries(vault.get("entries", []), path)


def _empty_vault() -> dict:
    """Create an empty vault structure."""
    return {"salt": "", "hash": "", "entries": []}


def add_entry(vault: dict, site: str, username: str, plaintext_password: str, key: bytes) -> dict:
    """Add an entry to the vault with encryption.

    Args:
        vault: The vault dict
        site: Website/service name
        username: Username or email
        plaintext_password: The plaintext password (will be encrypted)
        key: The Fernet key (from derive_key)

    Returns:
        Updated vault dict
    """
    encrypted = encrypt_password(plaintext_password, key)
    entry = {
        "id": str(uuid.uuid4()),
        "site": site,
        "username": username,
        "password": encrypted,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    vault["entries"].append(entry)
    return vault


def delete_entry(vault: dict, entry_id: str) -> dict:
    """Delete an entry from the vault by ID.

    Args:
        vault: The vault dict
        entry_id: UUID of the entry to delete

    Returns:
        Updated vault dict
    """
    vault["entries"] = [e for e in vault["entries"] if e["id"] != entry_id]
    return vault


def get_entries(vault: dict, key: bytes) -> list:
    """Get all entries from vault with passwords decrypted.

    Args:
        vault: The vault dict
        key: The Fernet key (from derive_key)

    Returns:
        List of entry dicts with decrypted passwords

    Raises:
        InvalidToken: If the key is wrong or a password is tampered
    """
    decrypted_entries = []
    for entry in vault["entries"]:
        try:
            plaintext = decrypt_password(entry["password"], key)
            decrypted_entries.append({
                "id": entry["id"],
                "site": entry["site"],
                "username": entry["username"],
                "password": plaintext,
            })
        except InvalidToken:
            raise InvalidToken(f"Failed to decrypt password for {entry['site']} — wrong key or tampered vault")

    return decrypted_entries