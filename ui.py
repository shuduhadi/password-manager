import customtkinter as ctk

from encryption import hash_master_password, verify_master_password, generate_salt, derive_key


from vault import load_vault, save_vault



# COLOUR PALETTE
BG_DARK = "#0b0b0f"
CARD_DARK = "#111116"
CARD_DARKER = "#0d0d12"

BORDER_DIM = "#29232d"
BORDER_ACTIVE = "#ff007f"

HOT_PINK = "#ff1493"
HOT_PINK_HOVER = "#ff4da6"

TEXT_PRIMARY = "#f5f5f5"
TEXT_SECONDARY = "#8b8491"
TEXT_MUTED = "#5f5865"

ERROR_RED = "#ff4d6d"

BLACK = "#08080b"



# CUSTOMTKINTER SETTINGS
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class LoginWindow:
    """
    PyVault login / setup screen.
    """

    WIDTH = 520
    HEIGHT = 600

    def __init__(self, vault_path: str = "vault.json"):

        self.vault_path = vault_path
        self.vault = load_vault(vault_path)
        self.key = None

      
        # MAIN WINDOW
        self.window = ctk.CTk()

        self.window.title("PyVault")
        self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        self.window.resizable(False, False)

        self.window.configure(
            fg_color=BG_DARK
        )

        # TOP BAR
        self._create_top_bar()

        # MAIN CONTENT
        self._create_main_area()

        # SELECT MODE
        if not self.vault.get("hash"):
            self._setup_mode()
        else:
            self._unlock_mode()

    
    def _create_top_bar(self):

        self.top_bar = ctk.CTkFrame(
            self.window,
            height=42,
            corner_radius=0,
            fg_color="#0d0d11",
            border_width=0,
        )

        self.top_bar.pack(
            fill="x",
            side="top"
        )

        # Pink indicator
        self.status_dot = ctk.CTkLabel(
            self.top_bar,
            text="●",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=9,
            ),
            text_color=HOT_PINK,
        )

        self.status_dot.pack(
            side="left",
            padx=(16, 6)
        )

        # Application name
        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="PyVault",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=12,
                weight="bold",
            ),
            text_color=TEXT_PRIMARY,
        )

        self.title_label.pack(
            side="left"
        )

        # Encryption status
        self.status_label = ctk.CTkLabel(
            self.top_bar,
            text="  encrypted vault",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=10,
            ),
            text_color=TEXT_MUTED,
        )

        self.status_label.pack(
            side="left"
        )

        # Bottom border
        self.top_border = ctk.CTkFrame(
            self.window,
            height=1,
            corner_radius=0,
            fg_color=BORDER_DIM,
        )

        self.top_border.pack(
            fill="x"
        )

    def _create_main_area(self):

        self.main = ctk.CTkFrame(
            self.window,
            fg_color=BG_DARK,
            corner_radius=0,
        )

        self.main.pack(
            fill="both",
            expand=True
        )

    def _create_card(self):

        self.card = ctk.CTkFrame(
            self.main,
            width=360,
            height=410,
            corner_radius=10,
            fg_color=CARD_DARK,
            border_width=1,
            border_color=BORDER_DIM,
        )

        self.card.place(
            relx=0.5,
            rely=0.48,
            anchor="center"
        )

        self.card.pack_propagate(False)

        self.card_accent = ctk.CTkFrame(
            self.card,
            height=2,
            corner_radius=0,
            fg_color=HOT_PINK,
        )

        self.card_accent.pack(
            fill="x",
            side="top"
        )

        self.inner = ctk.CTkFrame(
            self.card,
            fg_color="transparent",
        )

        self.inner.pack(
            fill="both",
            expand=True,
            padx=38,
            pady=30,
        )

    def _create_logo(self):

        logo_frame = ctk.CTkFrame(
            self.inner,
            fg_color="transparent",
        )

        logo_frame.pack(
            fill="x",
            pady=(0, 20)
        )

        # Lock symbol
        lock = ctk.CTkLabel(
            logo_frame,
            text="🔒",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=30,
                weight="bold",
            ),
            text_color=HOT_PINK,
        )

        lock.pack(
            side="left",
            padx=(0, 10)
        )

        logo_text = ctk.CTkFrame(
            logo_frame,
            fg_color="transparent",
        )

        logo_text.pack(
            side="left"
        )

        ctk.CTkLabel(
            logo_text,
            text="PYVAULT",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=16,
                weight="bold",
            ),
            text_color=TEXT_PRIMARY,
        ).pack(
            anchor="w"
        )

        ctk.CTkLabel(
            logo_text,
            text="PASSWORD MANAGER",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=8,
                weight="bold",
            ),
            text_color=HOT_PINK,
        ).pack(
            anchor="w"
        )


    def _create_input(
        self,
        parent,
        placeholder: str,
    ):

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            placeholder_text_color=TEXT_MUTED,

            show="•",

            height=42,

            corner_radius=6,

            fg_color=BLACK,

            text_color=TEXT_PRIMARY,

            border_width=1,

            border_color=BORDER_DIM,

            font=ctk.CTkFont(
                family="Segoe UI",
                size=12,
            ),
        )

        entry.pack(
            fill="x",
            pady=(0, 12)
        )

        self._bind_focus_glow(entry)

        return entry

    def _bind_focus_glow(self, entry):

        def focus_in(event):

            entry.configure(
                border_color=HOT_PINK,
                border_width=1,
            )

        def focus_out(event):

            entry.configure(
                border_color=BORDER_DIM,
                border_width=1,
            )

        entry.bind(
            "<FocusIn>",
            focus_in
        )

        entry.bind(
            "<FocusOut>",
            focus_out
        )


    def _create_button(
        self,
        text,
        command,
    ):

        button = ctk.CTkButton(
            self.inner,

            text=text,

            command=command,

            height=42,

            corner_radius=6,

            fg_color=HOT_PINK,

            hover_color=HOT_PINK_HOVER,

            text_color=BLACK,

            font=ctk.CTkFont(
                family="Segoe UI",
                size=12,
                weight="bold",
            ),

            border_width=0,
        )

        button.pack(
            fill="x",
            pady=(10, 0)
        )

        return button

    def _setup_mode(self):

        self._create_card()

        self._create_logo()

        ctk.CTkLabel(
            self.inner,
            text="Create master password",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
                weight="bold",
            ),
            text_color=TEXT_PRIMARY,
        ).pack(
            anchor="w",
            pady=(0, 4)
        )

        ctk.CTkLabel(
            self.inner,
            text="Your master password protects the vault.",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=10,
            ),
            text_color=TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(0, 18)
        )

        # Password

        self.password_entry = self._create_input(
            self.inner,
            "Password",
        )

        # Confirm

        self.confirm_entry = self._create_input(
            self.inner,
            "Confirm password",
        )

        # Error

        self.error_label = ctk.CTkLabel(
            self.inner,
            text="",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=10,
            ),
            text_color=ERROR_RED,
        )

        self.error_label.pack(
            anchor="w",
            pady=(0, 2)
        )

        # Button

        self._create_button(
            "Create vault  →",
            self._create_vault,
        )

        # Keyboard shortcuts

        self.password_entry.bind(
            "<Return>",
            lambda e: self._create_vault()
        )

        self.confirm_entry.bind(
            "<Return>",
            lambda e: self._create_vault()
        )

        self.password_entry.focus()

    def _unlock_mode(self):

        self.attempts = 0

        self._create_card()

        self._create_logo()

        ctk.CTkLabel(
            self.inner,
            text="Welcome back",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
                weight="bold",
            ),
            text_color=TEXT_PRIMARY,
        ).pack(
            anchor="w",
            pady=(0, 4)
        )

        ctk.CTkLabel(
            self.inner,
            text="Enter your master password to continue.",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=10,
            ),
            text_color=TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(0, 18)
        )

        self.password_entry = self._create_input(
            self.inner,
            "Master password",
        )

        self.error_label = ctk.CTkLabel(
            self.inner,
            text="",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=10,
            ),
            text_color=ERROR_RED,
        )

        self.error_label.pack(
            anchor="w",
            pady=(0, 2)
        )

        self._create_button(
            "Unlock vault  →",
            self._unlock_vault,
        )

        self.password_entry.bind(
            "<Return>",
            lambda e: self._unlock_vault()
        )

        self.password_entry.focus()

    def _create_vault(self):

        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        if len(password) < 8:

            self._show_error(
                "Password must contain at least 8 characters."
            )

            return

        if password != confirm:

            self._show_error(
                "Passwords do not match."
            )

            return

        salt = generate_salt()

        pw_hash = hash_master_password(
            password
        )

        self.key = derive_key(
            password,
            salt
        )

        self.vault["salt"] = salt.hex()

        self.vault["hash"] = pw_hash.decode()

        save_vault(
            self.vault,
            self.vault_path
        )

        self.window.destroy()


    def _unlock_vault(self):

        password = self.password_entry.get()

        stored_hash = self.vault["hash"].encode()

        stored_salt = bytes.fromhex(
            self.vault["salt"]
        )

        if verify_master_password(
            password,
            stored_hash
        ):

            self.key = derive_key(
                password,
                stored_salt
            )

            self.window.destroy()

        else:

            self.attempts += 1

            remaining = 3 - self.attempts

            if remaining > 0:

                self._show_error(
                    f"Incorrect password. "
                    f"{remaining} attempt"
                    f"{'s' if remaining != 1 else ''} remaining."
                )

                self.password_entry.delete(
                    0,
                    "end"
                )

            else:

                self._show_error(
                    "Too many failed attempts. Exiting..."
                )

                self.window.after(
                    1500,
                    lambda: (
                        self.window.destroy(),
                        exit(1)
                    )
                )

    def _show_error(self, message: str):

        self.error_label.configure(
            text=message
        )

    def run(self):

        self.window.mainloop()

if __name__ == "__main__":

    login = LoginWindow(
        "vault.json"
    )

    login.run()