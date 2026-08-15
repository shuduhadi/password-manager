import getpass
import sys
from encryption import hash_master_password, verify_master_password, generate_salt, derive_key
from vault import load_vault, save_vault, add_entry, delete_entry, get_entries
from cryptography.fernet import InvalidToken

VAULT_PATH = "vault.json"

def main():
    """Main CLI entry point"""
    print("=" * 50)
    print("PyVault - Encrypted Password Manager")
    print("=" * 50)

    vault = load_vault(VAULT_PATH)

    # First run: create master password
    if not vault.get("hash"):
        print("\n First run - creating master password.\n")
        master_password = get_master_password_setup()
        salt = generate_salt()
        pw_hash = hash_master_password(master_password)
        key = derive_key(master_password, salt)

        vault["salt"] = salt.hex()
        vault["hash"] = pw_hash.decode()
        save_vault(vault, VAULT_PATH)
        print("\n ✅ Master password set. vault created.\n")
    else:
        # Existing vault: unlock
        print("\nUnlock your vault 🔑\n")
        key = unlock_vault(vault)
        if key is None:
            print("\n c Failed to unlock vault. Exiting..\n")
            sys.exit(0)

    # Main Menu
    menu_loop(vault, key)

def get_master_password_setup() -> str:
    """Promot for new master password (twice to confirm)."""
    while True:
        password = getpass.getpass("Enter master password: ")
        if len(password) < 8:
            print("❌ Password too short (minimum 8 characters)\n")
            continue

        confirm = getpass.getpass("Confirm master password: ")
        if password != confirm:
            print("❌ Passwords don't match. Try again..\n")
            continue

        return password

def unlock_vault(vault: dict) -> bytes | None:
    """Prompt for master password and derive key. Return key or None if wrong."""

    stored_hash = vault["hash"].encode()
    stored_salt = bytes.fromhex(vault["salt"])
    for attempt in range(3):
        password = getpass.getpass("Master password: ")

        if verify_master_password(password, stored_hash):
            key = derive_key(password, stored_salt)
            print("🔓 Unlocked \n")
            return key
        else:
            remaining = 3 - attempt - 1
            if remaining > 0:
                print(f"❌ Wrong password. {remaining} attempts remaining.\n")
            else:
                print("❌ Too many failed attempts. Exiting..\n")

    return None

def menu_loop(vault: dict, key:bytes) -> None:
    """Main interactive menu"""
    while True:
        print("\n[1] ADD PASSWORD")
        print("\n[2] VIEW PASSWORDS")
        print("\n[3] DELETE PASSWORD")
        print("\n[4] EXIT")

        choice = input("\nChoice [1-4]: ").strip()

        if choice == "1":
            add_pass(vault,key)
        elif choice == "2":
            view_pass(vault,key)
        elif choice == "3":
            delete_pass(vault, key)
        elif choice == "4":
            save_vault(vault, VAULT_PATH)
            print("\n ✅ Vault saved. Goodbye.\n")
            sys.exit(0)
        else:
            print("Invalid choice. Try again\n")

def add_pass(vault:dict, key:bytes) -> None:
    """Add a new password to vault"""
    print()
    site = input("Website/service name: ").strip()
    username = input("Username or email: ").strip()
    password = getpass.getpass("Password: ")

    if not site or not username or not password:
        print(" ❌ All fields required. \n")
        return

    vault = add_entry(vault, site, username, password, key)
    save_vault(vault, VAULT_PATH)
    print(f"\n Password for '{site}' saved.\n")

def view_pass(vault:dict, key:bytes) -> None:
    """Display all saved passwords"""
    try:
        entries = get_entries(vault, key)
    except InvalidToken:
        print("\n Failed to decrypt - vault may be corrupted or key is wrong.\n")
        return

    if not entries:
        print("\n(No Saved passwords)\n")
        return

    print("\n" + "=" * 60)
    for i, entry in enumerate(entries,1):
        print(f"\n[{i}] {entry['site']}")
        print(f"Username: {entry['username']}")
        print(f"Password: {'*' * len(entry['password'])} (hidden)")
    print("\n" + "=" * 60)

def delete_pass(vault:dict, key:bytes) -> None:
    """Delete a password from vault."""
    try:
        entries = get_entries(vault, key)
    except InvalidToken:
        print("Failed to decrypt vault.\n")
        return

    if not entries:
        print("\n(No saved passwords)")
        return

    print()
    for i, entry in enumerate(entries, 1):
        print(f"[{i}] {entry['site']} ({entry['username']})")

    choice = input("\nDelete which? [1- {}}] (0 to cancel): ").format(len(entries)).strip()

    try:
        idx = int(choice)
        if idx == 0:
            return
    
        if 1 <= idx <= len(entries):
            entry_id = entries[idx - 1]["id"]
            vault = delete_entry(vault, entry_id)
            save_vault(vault, VAULT_PATH)
            print(f"\n✓ Deleted.\n")
        else:
                print("\n✗ Invalid choice.\n")
    except ValueError:
            print("\n✗ Invalid input.\n")
 
 
if __name__ == "__main__":
    main()



