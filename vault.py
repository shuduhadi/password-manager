import json
import uuid
from pathlib import Path
from encryption import encrypt_password, decrypt_password
from cryptography.fernet import InvalidToken


def load_vault(path: str = "vault.json") -> dict:
    """Load vault from file, or return empty vault if file doesn't exist.
    
    Args:
        path: Path to vault.json file
    
    Returns:
        Vault dict with structure:
        {
            "salt": str (hex),
            "hash": str (bcrypt hash as string),
            "entries": [
                {"id": str, "site": str, "username": str, "password": str (encrypted)},
                ...
            ]
        }
    """
    vault_path = Path(path)
    
    if not vault_path.exists():
        return _empty_vault()
    
    with open(vault_path, "r") as f:
        vault = json.load(f)
    
    return vault


def save_vault(vault: dict, path: str = "vault.json") -> None:
    """Save vault to file.
    
    Args:
        vault: Vault dict to save
        path: Path to write vault.json to
    """
    vault_path = Path(path)
    
    with open(vault_path, "w") as f:
        json.dump(vault, f, indent=2)


def _empty_vault() -> dict:
    """Create an empty vault structure."""
    return {
        "salt": "",
        "hash": "",
        "entries": []
    }


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
        "password": encrypted
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
                "password": plaintext
            })
        except InvalidToken:
            raise InvalidToken(f"Failed to decrypt password for {entry['site']} — wrong key or tampered vault")
    
    return decrypted_entries