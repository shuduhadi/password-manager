"""
Encrypted vault export/import (backup and restore).

Export decrypts every entry, packages them into one JSON payload, then
re-encrypts that whole payload with the vault's own key before writing
it to disk. The file also stores the vault's (non-secret) salt so the
same key can be re-derived from the master password alone at import
time — nothing in the file, including site/username, is readable
without the master password.
"""

import json
from cryptography.fernet import InvalidToken

from encryption import encrypt_password, decrypt_password, derive_key
from vault import get_entries, add_entry


BACKUP_FORMAT = "pyvault-backup"
BACKUP_VERSION = 1


class BackupPasswordError(Exception):
    """Raised when the wrong master password is given for a backup file."""


class BackupFormatError(Exception):
    """Raised when the file isn't a recognizable PyVault backup."""


def export_backup(vault: dict, key: bytes, file_path: str) -> int:
    """Write an encrypted backup of every entry in `vault` to `file_path`.

    Args:
        vault: The unlocked vault dict (must include "salt").
        key: The Fernet key currently unlocking this vault.
        file_path: Where to write the .vaultbak file.

    Returns:
        The number of entries written.
    """
    entries = get_entries(vault, key)  # decrypted: id, site, username, password

    payload = {
        "entries": [
            {
                "site": e["site"],
                "username": e["username"],
                "password": e["password"],
            }
            for e in entries
        ]
    }

    encrypted_blob = encrypt_password(json.dumps(payload), key)

    backup_file = {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "salt": vault["salt"],
        "data": encrypted_blob,
    }

    with open(file_path, "w") as f:
        json.dump(backup_file, f, indent=2)

    return len(payload["entries"])


def import_backup(file_path: str, master_password: str) -> list[dict]:
    """Decrypt a .vaultbak file and return its entries.

    Args:
        file_path: Path to the .vaultbak file.
        master_password: The master password used when it was exported.

    Returns:
        List of dicts: {"site", "username", "password"} — all plaintext.

    Raises:
        BackupFormatError: If the file isn't a valid/recognizable backup.
        BackupPasswordError: If the password is wrong for this backup.
    """
    try:
        with open(file_path, "r") as f:
            backup_file = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise BackupFormatError(f"Not a valid backup file: {exc}") from exc

    if not isinstance(backup_file, dict) or backup_file.get("format") != BACKUP_FORMAT:
        raise BackupFormatError("This file is not a recognized PyVault backup.")

    if "salt" not in backup_file or "data" not in backup_file:
        raise BackupFormatError("This backup file is missing required data.")

    try:
        salt = bytes.fromhex(backup_file["salt"])
    except ValueError as exc:
        raise BackupFormatError("This backup file's salt is corrupted.") from exc

    key = derive_key(master_password, salt)

    try:
        decrypted_json = decrypt_password(backup_file["data"], key)
    except InvalidToken as exc:
        raise BackupPasswordError("Incorrect master password for this backup.") from exc

    try:
        payload = json.loads(decrypted_json)
    except json.JSONDecodeError as exc:
        raise BackupFormatError("This backup file's contents are corrupted.") from exc

    return payload.get("entries", [])


def merge_entries(vault: dict, key: bytes, imported_entries: list[dict]) -> tuple[dict, int, int]:
    """Merge imported entries into `vault`, skipping duplicates.

    Duplicate match is on (site, username), case-insensitive and
    whitespace-trimmed. Imported entries are re-encrypted with the
    current vault's key (not whatever key the backup was made under).

    Args:
        vault: The current unlocked vault dict.
        key: The current vault's Fernet key.
        imported_entries: Plaintext entries from import_backup().

    Returns:
        (updated_vault, added_count, skipped_count)
    """
    existing = get_entries(vault, key)
    existing_keys = {
        (e["site"].strip().lower(), e["username"].strip().lower()) for e in existing
    }

    added = 0
    skipped = 0

    for entry in imported_entries:
        dedup_key = (entry["site"].strip().lower(), entry["username"].strip().lower())

        if dedup_key in existing_keys:
            skipped += 1
            continue

        vault = add_entry(vault, entry["site"], entry["username"], entry["password"], key)
        existing_keys.add(dedup_key)  # guards against duplicates within the import file itself
        added += 1

    return vault, added, skipped