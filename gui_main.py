"""GUI entry point — login, then dashboard."""
from ui import LoginWindow, DashboardWindow


def main():
    login = LoginWindow("vault.json")
    login.run()

    if login.key is not None:
        dashboard = DashboardWindow(login.vault, login.key, "vault.json")
        dashboard.run()


if __name__ == "__main__":
    main()