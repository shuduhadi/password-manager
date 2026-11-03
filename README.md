# 🔐 PyVault — local encrypted password manager

> A Python desktop app for securely storing and managing passwords.
> All credentials are encrypted with AES-128 and never stored in plaintext.

## Features
- Master password protected vault
- AES encryption via Fernet (cryptography library)
- Password generator with configurable length and charset
- Password strength meter
- Copy to clipboard with auto-clear
- Auto-lock after inactivity
- SQLite storage, with a migration script from the original JSON vault
- Vault backups
- Local storage — your data never leaves your machine
- Both a command-line interface and a desktop GUI

## Tech stack
| Component | Library |
|---|---|
| Encryption | cryptography (Fernet, PBKDF2) |
| Password hashing | bcrypt |
| Storage | sqlite3 (stdlib) |
| GUI | customtkinter |
| Clipboard | pyperclip |
| Secure random | secrets (stdlib) |
| Testing | pytest, pytest-cov |

## How encryption works
1. Your master password is hashed with bcrypt (never stored plaintext)
2. A Fernet key is derived from your password using PBKDF2 (480k iterations)
3. Each stored password is encrypted with that Fernet key
4. The key exists only in memory while the app is unlocked

## Installation
```bash
git clone https://github.com/shuduhadi/password-manager.git
cd password-manager
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
```bash
python gui_main.py   # desktop GUI
python main.py       # command-line version
```
On first run you'll be asked to create a master password (minimum 8 characters).

If you have a vault from the older JSON version, migrate it with:
```bash
python migrate_to_sqlite.py
```

## Running tests
```bash
pytest --cov
```

## Project structure
| File | Responsibility |
|---|---|
| `encryption.py` | bcrypt hashing, salt generation, PBKDF2 key derivation |
| `vault.py` | Add / delete / read encrypted entries |
| `db.py` | SQLite schema and queries |
| `password_generator.py` | Secure password generation |
| `backup.py` | Vault backups |
| `migrate_to_sqlite.py` | One-off JSON → SQLite migration |
| `main.py` | CLI entry point |
| `gui_main.py`, `ui.py` | Desktop GUI |
| `tests/` | pytest suite |

## Future improvements
- [x] SQLite backend
- [ ] Export / import vault
- [ ] PyQt6 UI upgrade
- [ ] Browser extension
- [ ] Screenshots in this README

## Repository Verification

Verification Code: **WTC-HJQJZEZ6**
