"""GUI version of password manager using CustomTkinter.

Issue #8 scope: login screen only. Once logged in, this just
prints a confirmation — the real DashboardWindow lands in Issue #9.
"""
from ui import LoginWindow


def main():
    """Launch the GUI, show login/setup, confirm success."""
    login = LoginWindow("vault.json")
    login.run()

    if login.key is not None:
        print("✓ Login successful. Key derived. (Dashboard comes in Issue #9)")
    else:
        print("✗ Login was not completed.")


if __name__ == "__main__":
    main()