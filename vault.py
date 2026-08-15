import json
import uuid
from pathlib import Path

def load_vault(path: str = "vault.json") -> dict:
    # Load vault from file or return empty vault if file doesn't exist
    vault_path = Path(path)
    if not vault_path.exists():
        return empty_vault()

    with open(vault_path, "r") as f:
        vault = json.load(f)

        return vault

def save_vault(vault: dict, path: str = "vault.json") -> None:
    # Save vault to file
    vault_path = Path(path)
    with open(vault_path, "w") as f:
        json.dump(vault, f, indent=2)

def empty_vault() -> dict:
    # Creates an empty vault structure
    return {
        "salt":"",
        "hash":"",
        "entries":[]
    }

def add_entry(vault: dict, site: str, username: str, encrypted_password:str) -> dict:
    # Adds an entry to the vault
    entry = {
        "id": str(uuid.uuid4()),
        "site": site,
        "username": username,
        "password": encrypted_password
    }
    vault["entries"].append(entry)
    return vault

def delete_entry(vault: dict, entry_id: str) -> dict:
    # Deletes an entry from the vaulr by ID
    vault["entries"] = [e for e in vault["entries"] if e["id"] != entry_id]
    return vault

def get_entries(vault: dict) -> list:
    # Gets all entries from the vault
    return vault["entries"]