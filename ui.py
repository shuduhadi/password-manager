import customtkinter as ctk

from encryption import hash_master_password, verify_master_password, generate_salt, derive_key
from vault import load_vault, save_vault, add_entry, delete_entry, get_entries

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

# COLOUR PALETTE
BG_DARK = "#08080b"
BG_SIDEBAR = "#0d0b10"

CARD_DARK = "#111014"
CARD_HOVER = "#18141b"

INPUT_DARK = "#0b0a0e"

BORDER_DIM = "#28202d"
BORDER_HOVER = "#493247"

HOT_PINK = "#ff007f"
HOT_PINK_HOVER = "#ff4da6"

TEXT_PRIMARY = "#f5f5f5"
TEXT_SECONDARY = "#a39aaa"
TEXT_MUTED = "#6d6572"

ERROR_RED = "#ff4d6d"

WHITE = "#ffffff"
BLACK = "#08080b"


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class ConfirmDialog:
    """
    A themed modal dialog for confirmations and simple messages.

    Use ConfirmDialog.ask(parent, title, message) -> bool for
    yes/no confirmations, or ConfirmDialog.show(parent, title, message,
    kind="error"/"info") for a single-button notice.
    """

    WIDTH = 380

    def __init__(self, parent, title: str, message: str, mode: str = "confirm", kind: str = "info"):
        self.result = False

        self.window = ctk.CTkToplevel(parent)
        self.window.title(title)
        self.window.resizable(False, False)
        self.window.configure(fg_color=BG_DARK)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._on_no)

        accent_color = ERROR_RED if kind == "error" else HOT_PINK
        ctk.CTkFrame(self.window, height=2, corner_radius=0, fg_color=accent_color).pack(fill="x", side="top")

        inner = ctk.CTkFrame(self.window, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=26, pady=22)

        icon = "!" if kind == "error" else "i"
        icon_badge = ctk.CTkFrame(
            inner, width=34, height=34, corner_radius=17,
            fg_color="#1c111b", border_width=1, border_color=accent_color,
        )
        icon_badge.pack(anchor="w", pady=(0, 12))
        icon_badge.pack_propagate(False)
        ctk.CTkLabel(
            icon_badge, text=icon,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=accent_color,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            inner, text=message,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_SECONDARY,
            wraplength=self.WIDTH - 60, justify="left",
        ).pack(anchor="w", pady=(0, 20))

        button_row = ctk.CTkFrame(inner, fg_color="transparent")
        button_row.pack(fill="x")

        if mode == "confirm":
            ctk.CTkButton(
                button_row, text="No", command=self._on_no,
                height=38, corner_radius=7,
                fg_color="transparent", hover_color=CARD_HOVER,
                text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER_DIM,
                font=ctk.CTkFont(family="Segoe UI", size=11),
            ).pack(side="left", fill="x", expand=True, padx=(0, 6))

            ctk.CTkButton(
                button_row, text="Yes", command=self._on_yes,
                height=38, corner_radius=7,
                fg_color=accent_color, hover_color=HOT_PINK_HOVER,
                text_color=BLACK,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                border_width=0,
            ).pack(side="left", fill="x", expand=True, padx=(6, 0))
        else:
            ctk.CTkButton(
                button_row, text="OK", command=self._on_yes,
                height=38, corner_radius=7,
                fg_color=accent_color, hover_color=HOT_PINK_HOVER,
                text_color=BLACK,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                border_width=0,
            ).pack(fill="x")

        self.window.update_idletasks()
        self._center_on_parent(parent)

    def _center_on_parent(self, parent):
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.window.geometry(f"+{x}+{y}")

    def _on_yes(self):
        self.result = True
        self.window.grab_release()
        self.window.destroy()

    def _on_no(self):
        self.result = False
        self.window.grab_release()
        self.window.destroy()

    @staticmethod
    def ask(parent, title: str, message: str) -> bool:
        """Show a yes/no confirmation dialog and block until answered."""
        dialog = ConfirmDialog(parent, title, message, mode="confirm", kind="confirm")
        parent.wait_window(dialog.window)
        return dialog.result

    @staticmethod
    def show(parent, title: str, message: str, kind: str = "info") -> None:
        """Show a single-button notice dialog (info or error) and block until dismissed."""
        dialog = ConfirmDialog(parent, title, message, mode="notice", kind=kind)
        parent.wait_window(dialog.window)

class LoginWindow:
    """Login / first-time setup screen."""

    WIDTH = 520
    HEIGHT = 600

    def __init__(self, vault_path: str = "vault.json"):
        self.vault_path = vault_path
        self.vault = load_vault(vault_path)
        self.key = None

        self.window = ctk.CTk()
        self.window.title("PyVault")
        self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.window.resizable(False, False)
        self.window.configure(fg_color=BG_DARK)

        self._create_header()
        self._create_login_card()

        if not self.vault.get("hash"):
            self._setup_mode()
        else:
            self._unlock_mode()

    def _create_header(self):
        header = ctk.CTkFrame(self.window, height=54, corner_radius=0, fg_color=BG_DARK)
        header.pack(fill="x", side="top")

        ctk.CTkLabel(
            header, text="✦", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=HOT_PINK,
        ).pack(side="left", padx=(22, 8))

        ctk.CTkLabel(
            header, text="PyVault", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="  •  Password Manager", font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_MUTED,
        ).pack(side="left")

        ctk.CTkFrame(self.window, height=1, corner_radius=0, fg_color=BORDER_DIM).pack(fill="x")

    def _create_login_card(self):
        self.card = ctk.CTkFrame(
            self.window, width=380, height=430, corner_radius=14,
            fg_color=CARD_DARK, border_width=1, border_color=BORDER_DIM,
        )
        self.card.place(relx=0.5, rely=0.53, anchor="center")
        self.card.pack_propagate(False)

        ctk.CTkFrame(self.card, height=3, corner_radius=0, fg_color=HOT_PINK).pack(fill="x", side="top")

        self.inner = ctk.CTkFrame(self.card, fg_color="transparent")
        self.inner.pack(fill="both", expand=True, padx=38, pady=32)

    def _create_logo(self):
        logo_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(0, 22))

        ctk.CTkLabel(
            logo_frame, text="✦", font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            text_color=HOT_PINK,
        ).pack(side="left", padx=(0, 12))

        text_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        text_frame.pack(side="left")

        ctk.CTkLabel(
            text_frame, text="PyVault", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_frame, text="Your passwords, secured.", font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

    def _create_input(self, parent, placeholder):
        entry = ctk.CTkEntry(
            parent, placeholder_text=placeholder, placeholder_text_color=TEXT_MUTED,
            show="•", height=42, corner_radius=7,
            fg_color=INPUT_DARK, text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER_DIM,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        entry.pack(fill="x", pady=(0, 12))
        self._bind_focus(entry)
        return entry

    def _bind_focus(self, entry):
        entry.bind("<FocusIn>", lambda event: entry.configure(border_color=HOT_PINK))
        entry.bind("<FocusOut>", lambda event: entry.configure(border_color=BORDER_DIM))

    def _create_main_button(self, text, command):
        button = ctk.CTkButton(
            self.inner, text=text, command=command,
            height=42, corner_radius=7,
            fg_color=HOT_PINK, hover_color=HOT_PINK_HOVER,
            text_color=BLACK,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            border_width=0,
        )
        button.pack(fill="x", pady=(12, 0))
        return button

    def _setup_mode(self):
        self._create_logo()

        ctk.CTkLabel(
            self.inner, text="Create your master password",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            self.inner, text="This password will be used to unlock your encrypted vault.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_SECONDARY, wraplength=300, justify="left",
        ).pack(anchor="w", pady=(0, 18))

        self.password_entry = self._create_input(self.inner, "Master password")
        self.confirm_entry = self._create_input(self.inner, "Confirm master password")

        self.error_label = ctk.CTkLabel(
            self.inner, text="", font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=ERROR_RED, wraplength=300, justify="left",
        )
        self.error_label.pack(anchor="w")

        self._create_main_button("Create Vault", self._create_vault)

        self.password_entry.bind("<Return>", lambda event: self._create_vault())
        self.confirm_entry.bind("<Return>", lambda event: self._create_vault())
        self.password_entry.focus()

    def _unlock_mode(self):
        self.attempts = 0
        self._create_logo()

        ctk.CTkLabel(
            self.inner, text="Welcome back",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            self.inner, text="Enter your master password to unlock your vault.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 18))

        self.password_entry = self._create_input(self.inner, "Master password")

        self.error_label = ctk.CTkLabel(
            self.inner, text="", font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=ERROR_RED, wraplength=300, justify="left",
        )
        self.error_label.pack(anchor="w")

        self._create_main_button("Unlock Vault", self._unlock_vault)

        self.password_entry.bind("<Return>", lambda event: self._unlock_vault())
        self.password_entry.focus()

    def _create_vault(self):
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        if len(password) < 8:
            self._show_error("Password must contain at least 8 characters.")
            return

        if password != confirm:
            self._show_error("Passwords do not match.")
            return

        salt = generate_salt()
        pw_hash = hash_master_password(password)
        self.key = derive_key(password, salt)

        self.vault["salt"] = salt.hex()
        self.vault["hash"] = pw_hash.decode()
        save_vault(self.vault, self.vault_path)

        self.window.destroy()

    def _unlock_vault(self):
        password = self.password_entry.get()
        stored_hash = self.vault["hash"].encode()
        stored_salt = bytes.fromhex(self.vault["salt"])

        if verify_master_password(password, stored_hash):
            self.key = derive_key(password, stored_salt)
            self.window.destroy()
            return

        self.attempts += 1
        remaining = 3 - self.attempts

        if remaining > 0:
            self._show_error(
                f"Incorrect password. {remaining} attempt{'s' if remaining != 1 else ''} remaining."
            )
            self.password_entry.delete(0, "end")
        else:
            self._show_error("Too many failed attempts. Exiting...")
            self.window.after(1500, lambda: (self.window.destroy(), exit(1)))

    def _show_error(self, message: str):
        self.error_label.configure(text=message)

    def run(self):
        self.window.mainloop()

class DashboardWindow:
    """Main password manager dashboard."""

    WIDTH = 900
    HEIGHT = 650

    def __init__(self, vault: dict, key: bytes, vault_path: str = "vault.json"):
        self.vault = vault
        self.key = key
        self.vault_path = vault_path

        self._reveal_jobs = {}
        self._copy_reset_jobs = {}

        self.window = ctk.CTk()
        self.window.title("PyVault")
        self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.window.minsize(760, 520)
        self.window.configure(fg_color=BG_DARK)

        self._create_header()
        self._create_body()
        self._create_sidebar()
        self._create_content()
        self._create_status_bar()

        self.window.protocol("WM_DELETE_WINDOW", self._exit)

        self._refresh_list()

    def _create_header(self):
        header = ctk.CTkFrame(self.window, height=58, corner_radius=0, fg_color=BG_DARK)
        header.pack(fill="x", side="top")

        ctk.CTkLabel(
            header, text="✦", font=ctk.CTkFont(family="Segoe UI", size=21, weight="bold"),
            text_color=HOT_PINK,
        ).pack(side="left", padx=(22, 9))

        ctk.CTkLabel(
            header, text="PyVault", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Password Manager", font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_MUTED,
        ).pack(side="left", padx=(10, 0))

        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.pack(side="right", padx=20)

        ctk.CTkLabel(
            status_frame, text="●", font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=HOT_PINK,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            status_frame, text="Vault unlocked", font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_SECONDARY,
        ).pack(side="left")

        ctk.CTkFrame(self.window, height=1, corner_radius=0, fg_color=BORDER_DIM).pack(fill="x")

    def _create_body(self):
        self.body = ctk.CTkFrame(self.window, fg_color=BG_DARK, corner_radius=0)
        self.body.pack(fill="both", expand=True)

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.body, width=190, corner_radius=0, fg_color=BG_SIDEBAR, border_width=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar, text="LIBRARY", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(25, 12))

        self._create_sidebar_item(icon="🔑", text="Passwords", active=True)
        self._create_sidebar_item(icon="▣", text="All passwords", active=False)

        ctk.CTkFrame(self.sidebar, height=1, corner_radius=0, fg_color=BORDER_DIM).pack(
            fill="x", padx=20, pady=18
        )

        ctk.CTkLabel(
            self.sidebar, text="SECURITY", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self._create_sidebar_item(icon="🛡", text="Security", active=False)
        self._create_sidebar_item(icon="⚙", text="Settings", active=False)

    def _create_sidebar_item(self, icon, text, active=False):
        frame = ctk.CTkFrame(
            self.sidebar, height=40, corner_radius=7,
            fg_color="#1b111a" if active else "transparent",
        )
        frame.pack(fill="x", padx=12, pady=2)

        if active:
            ctk.CTkFrame(frame, width=3, corner_radius=2, fg_color=HOT_PINK).pack(
                side="left", fill="y", pady=8
            )

        ctk.CTkLabel(
            frame, text=icon, font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=HOT_PINK if active else TEXT_MUTED,
        ).pack(side="left", padx=(12, 9))

        ctk.CTkLabel(
            frame, text=text,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if active else "normal"),
            text_color=TEXT_PRIMARY if active else TEXT_SECONDARY,
        ).pack(side="left")

    def _create_content(self):
        self.content = ctk.CTkFrame(self.body, fg_color=BG_DARK, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(25, 18))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")

        ctk.CTkLabel(
            title_frame, text="My Passwords",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        self.count_label = ctk.CTkLabel(
            title_frame, text="", font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_SECONDARY,
        )
        self.count_label.pack(anchor="w", pady=(3, 0))

        ctk.CTkButton(
            header, text="+ Add password", command=self._open_add_dialog,
            width=145, height=38, corner_radius=7,
            fg_color=HOT_PINK, hover_color=HOT_PINK_HOVER,
            text_color=BLACK,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            border_width=0,
        ).pack(side="right")

        search_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        search_frame.pack(fill="x", padx=28, pady=(0, 15))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._refresh_list())

        self.search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.search_var,
            placeholder_text="Search your passwords...", placeholder_text_color=TEXT_MUTED,
            height=40, corner_radius=7,
            fg_color=INPUT_DARK, text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER_DIM,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self.search_entry.pack(fill="x")
        self._bind_focus(self.search_entry)

        self.scroll_frame = ctk.CTkScrollableFrame(
            self.content, fg_color=BG_DARK, corner_radius=0,
            scrollbar_button_color=BORDER_DIM, scrollbar_button_hover_color=HOT_PINK,
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

    def _create_status_bar(self):
        status = ctk.CTkFrame(self.window, height=27, corner_radius=0, fg_color="#0d0b10")
        status.pack(fill="x", side="bottom")

        ctk.CTkLabel(
            status, text="🔒  Your vault is encrypted", font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=TEXT_MUTED,
        ).pack(side="left", padx=14)

        ctk.CTkLabel(
            status, text="Local vault", font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=HOT_PINK,
        ).pack(side="right", padx=14)

    def _bind_focus(self, entry):
        entry.bind("<FocusIn>", lambda event: entry.configure(border_color=HOT_PINK))
        entry.bind("<FocusOut>", lambda event: entry.configure(border_color=BORDER_DIM))

    def _refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        try:
            entries = get_entries(self.vault, self.key)
        except Exception:
            self._show_toast("Vault error", "Failed to decrypt vault entries.", error=True)
            return

        query = self.search_var.get().strip().lower()
        if query:
            entries = [
                entry for entry in entries
                if query in entry["site"].lower() or query in entry["username"].lower()
            ]

        self.count_label.configure(
            text=f"{len(entries)} saved password{'s' if len(entries) != 1 else ''}"
        )

        if not entries:
            empty_card = ctk.CTkFrame(
                self.scroll_frame, fg_color=CARD_DARK, corner_radius=10,
                border_width=1, border_color=BORDER_DIM,
            )
            empty_card.pack(fill="x", padx=4, pady=20)

            ctk.CTkLabel(
                empty_card, text="🔐", font=ctk.CTkFont(family="Segoe UI Emoji", size=26),
                text_color=HOT_PINK,
            ).pack(pady=(25, 8))

            ctk.CTkLabel(
                empty_card, text="No matching passwords." if query else "Your vault is empty.",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color=TEXT_PRIMARY,
            ).pack()

            ctk.CTkLabel(
                empty_card,
                text="Try a different search." if query else "Add your first password to get started.",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=TEXT_SECONDARY,
            ).pack(pady=(4, 25))

            return

        for entry in entries:
            self._render_entry_card(entry)

    def _render_entry_card(self, entry: dict):
        card = ctk.CTkFrame(
            self.scroll_frame, fg_color=CARD_DARK, corner_radius=10,
            border_width=1, border_color=BORDER_DIM,
        )
        card.pack(fill="x", padx=4, pady=(0, 9))

        main = ctk.CTkFrame(card, fg_color="transparent")
        main.pack(fill="x", padx=15, pady=13)

        icon = ctk.CTkFrame(main, width=42, height=42, corner_radius=10, fg_color="#1c111b")
        icon.pack(side="left")
        icon.pack_propagate(False)

        ctk.CTkLabel(
            icon, text="🔑", font=ctk.CTkFont(family="Segoe UI Emoji", size=16),
            text_color=HOT_PINK,
        ).place(relx=0.5, rely=0.5, anchor="center")

        details = ctk.CTkFrame(main, fg_color="transparent")
        details.pack(side="left", fill="both", expand=True, padx=(13, 10))

        ctk.CTkLabel(
            details, text=entry["site"], font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            details, text=entry["username"], font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_SECONDARY, anchor="w",
        ).pack(anchor="w", pady=(2, 5))

        masked = "•" * min(len(entry["password"]), 20)
        password_label = ctk.CTkLabel(
            details, text=masked, font=ctk.CTkFont(family="Consolas", size=11),
            text_color=TEXT_MUTED, anchor="w",
        )
        password_label.pack(anchor="w")

        actions = ctk.CTkFrame(main, fg_color="transparent")
        actions.pack(side="right")

        copy_button = self._create_action_button(
            actions, "Copy", HOT_PINK, lambda: self._copy_password(entry, copy_button)
        )
        copy_button.pack(side="left", padx=(0, 5))

        reveal_button = self._create_action_button(
            actions, "Reveal", TEXT_SECONDARY,
            lambda: self._toggle_reveal(entry, password_label, reveal_button, masked),
        )
        reveal_button.pack(side="left", padx=(0, 5))

        delete_button = self._create_action_button(
            actions, "Delete", ERROR_RED, lambda: self._confirm_delete(entry)
        )
        delete_button.pack(side="left")

        self._add_card_hover(card)

    def _create_action_button(self, parent, text, text_color, command):
        return ctk.CTkButton(
            parent, text=text, command=command,
            width=62, height=29, corner_radius=6,
            fg_color="transparent", hover_color=CARD_HOVER,
            text_color=text_color, border_width=1, border_color=BORDER_DIM,
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
        )

    def _add_card_hover(self, card):
        def enter(event):
            card.configure(border_color=BORDER_HOVER)

        def leave(event):
            card.configure(border_color=BORDER_DIM)

        card.bind("<Enter>", enter, add="+")
        card.bind("<Leave>", leave, add="+")

    def _copy_password(self, entry: dict, button: ctk.CTkButton):
        if not HAS_CLIPBOARD:
            self._show_toast("Clipboard unavailable", "pyperclip is not installed.", error=True)
            return

        pyperclip.copy(entry["password"])
        button.configure(text="Copied!", text_color=HOT_PINK)

        entry_id = entry["id"]
        if entry_id in self._copy_reset_jobs:
            self.window.after_cancel(self._copy_reset_jobs[entry_id])

        def reset_button():
            try:
                button.configure(text="Copy", text_color=HOT_PINK)
            except Exception:
                pass

        self._copy_reset_jobs[entry_id] = self.window.after(2000, reset_button)

        def clear_clipboard():
            try:
                if pyperclip.paste() == entry["password"]:
                    pyperclip.copy("")
            except Exception:
                pass

        self.window.after(30000, clear_clipboard)

    def _toggle_reveal(self, entry, label, button, masked):
        entry_id = entry["id"]
        is_revealed = entry_id in self._reveal_jobs

        if is_revealed:
            self.window.after_cancel(self._reveal_jobs[entry_id])
            del self._reveal_jobs[entry_id]
            label.configure(text=masked)
            button.configure(text="Reveal")
            return

        label.configure(text=entry["password"])
        button.configure(text="Hide")

        def auto_hide():
            try:
                label.configure(text=masked)
                button.configure(text="Reveal")
            except Exception:
                pass
            self._reveal_jobs.pop(entry_id, None)

        self._reveal_jobs[entry_id] = self.window.after(5000, auto_hide)

    def _confirm_delete(self, entry: dict):
        confirmed = ConfirmDialog.ask(
            self.window,
            "Delete password",
            f"Delete the saved password for '{entry['site']}' ({entry['username']})? "
            f"This cannot be undone.",
        )
        if not confirmed:
            return

        self.vault = delete_entry(self.vault, entry["id"])
        save_vault(self.vault, self.vault_path)
        self._refresh_list()

    def _open_add_dialog(self):
        AddPasswordDialog(self.window, self.vault, self.key, self.vault_path, on_saved=self._refresh_list)

    def _show_toast(self, title: str, message: str, error: bool = False):
        ConfirmDialog.show(self.window, title, message, kind="error" if error else "info")

    def _exit(self):
        save_vault(self.vault, self.vault_path)
        self.window.destroy()

    def run(self):
        self.window.mainloop()

class AddPasswordDialog:
    """Dialog for adding a new password."""

    WIDTH = 430
    HEIGHT = 470

    def __init__(self, parent, vault: dict, key: bytes, vault_path: str, on_saved):
        self.vault = vault
        self.key = key
        self.vault_path = vault_path
        self.on_saved = on_saved

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Add Password — PyVault")
        self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.window.resizable(False, False)
        self.window.configure(fg_color=BG_DARK)
        self.window.transient(parent)
        self.window.grab_set()

        header = ctk.CTkFrame(self.window, height=58, corner_radius=0, fg_color=BG_DARK)
        header.pack(fill="x")

        ctk.CTkLabel(
            header, text="✦", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=HOT_PINK,
        ).pack(side="left", padx=(22, 8))

        ctk.CTkLabel(
            header, text="Add Password", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkFrame(self.window, height=1, corner_radius=0, fg_color=BORDER_DIM).pack(fill="x")

        inner = ctk.CTkFrame(self.window, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=26)

        ctk.CTkLabel(
            inner, text="Save a new password", font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text="Your credentials will be stored inside your encrypted vault.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(4, 20))

        self.site_entry = self._make_input(inner, "Website or service")
        self.username_entry = self._make_input(inner, "Username or email")
        self.password_entry = self._make_input(inner, "Password", show="•")

        self.error_label = ctk.CTkLabel(
            inner, text="", font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=ERROR_RED,
        )
        self.error_label.pack(anchor="w", pady=(2, 0))

        button_row = ctk.CTkFrame(inner, fg_color="transparent")
        button_row.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(
            button_row, text="Cancel", command=self.window.destroy,
            height=40, corner_radius=7,
            fg_color="transparent", hover_color=CARD_HOVER,
            text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER_DIM,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            button_row, text="Save Password", command=self._save,
            height=40, corner_radius=7,
            fg_color=HOT_PINK, hover_color=HOT_PINK_HOVER,
            text_color=BLACK,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            border_width=0,
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.site_entry.focus()

    def _make_input(self, parent, placeholder, show=""):
        entry = ctk.CTkEntry(
            parent, placeholder_text=placeholder, placeholder_text_color=TEXT_MUTED,
            show=show, height=40, corner_radius=7,
            fg_color=INPUT_DARK, text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER_DIM,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        entry.pack(fill="x", pady=(0, 11))

        entry.bind("<FocusIn>", lambda event: entry.configure(border_color=HOT_PINK))
        entry.bind("<FocusOut>", lambda event: entry.configure(border_color=BORDER_DIM))
        entry.bind("<Return>", lambda event: self._save())

        return entry

    def _save(self):
        site = self.site_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not site or not username or not password:
            self.error_label.configure(text="All fields are required.")
            return

        self.vault = add_entry(self.vault, site, username, password, self.key)
        save_vault(self.vault, self.vault_path)

        if self.on_saved:
            self.on_saved()

        self.window.destroy()


if __name__ == "__main__":
    login = LoginWindow("vault.json")
    login.run()

    if login.key is not None:
        dashboard = DashboardWindow(login.vault, login.key, "vault.json")
        dashboard.run()