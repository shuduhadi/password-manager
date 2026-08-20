"""GUI entry point — login, then dashboard.

Loops back to the login/unlock screen whenever the dashboard locks
itself (auto-lock timeout or the manual "Lock now" button), instead
of exiting the whole app. A real quit (closing the window via Exit,
or the OS window-close button) ends the loop normally.
"""
from ui import LoginWindow, DashboardWindow

VAULT_PATH = "vault.json"


def main():
    while True:
        login = LoginWindow(VAULT_PATH)
        login.run()

        if login.key is None:
            # Setup/unlock was abandoned or failed out — exit the app.
            break

        dashboard = DashboardWindow(login.vault, login.key, VAULT_PATH)
        dashboard.run()

        if not dashboard.locked_out:
            # User chose Exit / closed the window normally — done.
            break

        # Otherwise the vault was locked (auto-lock or manual Lock now) —
        # loop back around to the login screen to unlock again.


if __name__ == "__main__":
    main()