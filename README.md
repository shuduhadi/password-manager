
# PyVault — local encrypted password manager

> A Python desktop app for securely storing and managing passwords.
> All credentials are encrypted with AES-128 and never stored in plaintext.

## Screenshots
[Login screen] [Dashboard] [Password generator]

## Features
- Master password protected vault
- AES encryption via Fernet (cryptography library)
- Password generator with configurable length and charset
- Password strength meter
- Copy to clipboard with auto-clear
- Auto-lock after inactivity
- Local storage — your data never leaves your machine

## Tech stack
| Component | Library |
|---|---|
| Encryption | cryptography (Fernet, PBKDF2) |
| Password hashing | bcrypt |
| GUI | tkinter |
| Clipboard | pyperclip |
| Secure random | secrets (stdlib) |

## How encryption works
1. Your master password is hashed with bcrypt (never stored plaintext)
2. A Fernet key is derived from your password using PBKDF2 (480k iterations)
3. Each stored password is encrypted with that Fernet key
4. The key exists only in memory while the app is unlocked

## Installation
```
git clone https://github.com/shuduhadi/pyvault
cd pyvault
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Future improvements
- [ ] SQLite backend
- [ ] Export / import vault
- [ ] PyQt6 UI upgrade
- [ ] Browser extension
