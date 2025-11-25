import customtkinter as ctk

from clinic_app.config import init_theme
from clinic_app.db_mysql import verify_user
from clinic_app.ui.dashboard import DashboardFrame


class DentalApp(ctk.CTk):
    """Root application that opens on the login page."""

    def __init__(self) -> None:
        super().__init__()
        init_theme()
        self.title("Dental Clinic System")
        self.geometry("980x620")
        self.minsize(900, 560)
        # Deep background to let cards pop.
        self.configure(fg_color="#0b1220")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._current_body: ctk.CTkFrame | None = None
        self._build_header()
        self._show_login()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Aurora Dental",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#e5e7eb",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Clinical tools, simplified.",
            font=ctk.CTkFont(size=14),
            text_color="#9ca3af",
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

    def _clear_body(self) -> None:
        if self._current_body is not None:
            self._current_body.destroy()
            self._current_body = None

    def _show_login(self) -> None:
        self._clear_body()
        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.grid(row=1, column=0, sticky="nsew", padx=24, pady=16)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(shell, corner_radius=18, fg_color="#0f172a", border_color="#1f2937", border_width=1)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)

        body = ctk.CTkFrame(card, corner_radius=14, fg_color="#0b1220")
        body.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        body.grid_columnconfigure(0, weight=1)

        # Minimal header with logo mark
        logo = ctk.CTkFrame(body, width=64, height=64, corner_radius=12, fg_color="#0ea5e9")
        logo.grid_propagate(False)
        logo.grid(row=0, column=0, pady=(6, 10))
        ctk.CTkLabel(
            logo,
            text="DC",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#0b1220",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            body,
            text="Dental Clinic",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#e5e7eb",
        ).grid(row=1, column=0, sticky="n", pady=(0, 4))

        ctk.CTkLabel(
            body,
            text="Sign in to continue",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
        ).grid(row=2, column=0, sticky="n", pady=(0, 14))

        form = ctk.CTkFrame(body, corner_radius=12, fg_color="#111827")
        form.grid(row=3, column=0, sticky="ew", padx=12, pady=4)
        form.grid_columnconfigure(0, weight=1)

        username_entry = ctk.CTkEntry(form, placeholder_text="Username", height=40)
        username_entry.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")

        password_entry = ctk.CTkEntry(form, placeholder_text="Password", show="*", height=40)
        password_entry.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        status_label = ctk.CTkLabel(form, text="", text_color="#f97316")
        status_label.grid(row=3, column=0, sticky="w", padx=12, pady=(4, 10))

        def submit_login() -> None:
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            if not username or not password:
                status_label.configure(text="Enter username and password.")
                return
            status_label.configure(text="Checking...")
            self.update_idletasks()

            ok, message, role = verify_user(username, password)
            if not ok:
                status_label.configure(text=message)
                return

            status_label.configure(text="")
            self._show_dashboard(username=f"{username} ({role or 'user'})")

        ctk.CTkButton(
            form,
            text="Continue",
            command=submit_login,
            height=42,
            fg_color="#0ea5e9",
            hover_color="#0284c7",
            text_color="#0b1220",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=2, column=0, padx=12, pady=(4, 6), sticky="ew")

        ctk.CTkLabel(
            form,
            text="Authorized staff only.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        ).grid(row=4, column=0, sticky="w", padx=12, pady=(0, 12))

        self._current_body = shell

    def _show_dashboard(self, username: str) -> None:
        self._clear_body()
        dashboard = DashboardFrame(self, username=username)
        dashboard.grid(row=1, column=0, sticky="nsew", padx=24, pady=16)
        self._current_body = dashboard


def run() -> None:
    app = DentalApp()
    app.mainloop()
