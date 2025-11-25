import customtkinter as ctk

from clinic_app.db_mysql import fetch_patients


def open_patient_history_window(master: ctk.CTkBaseClass) -> ctk.CTkToplevel:
    """Open a window showing all patients from the database."""
    ok, msg, rows = fetch_patients()

    win = ctk.CTkToplevel(master)
    win.title("Patient history")
    win.geometry("900x520")
    win.grid_columnconfigure(0, weight=1)
    win.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(
        win, text="Patient history", font=ctk.CTkFont(size=20, weight="bold")
    ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

    if not ok:
        ctk.CTkLabel(win, text=msg, text_color="orange").grid(
            row=1, column=0, padx=12, pady=12, sticky="w"
        )
        return win

    scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
    scroll.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
    scroll.grid_columnconfigure(0, weight=1)

    if not rows:
        ctk.CTkLabel(scroll, text="No patient records found.").grid(
            row=0, column=0, padx=8, pady=8, sticky="w"
        )
        return win

    # Build table headers from keys
    headers = list(rows[0].keys())
    header_frame = ctk.CTkFrame(scroll, fg_color="#0f172a")
    header_frame.grid(row=0, column=0, sticky="ew")
    for idx, h in enumerate(headers):
        ctk.CTkLabel(
            header_frame,
            text=h,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=idx, padx=6, pady=6, sticky="w")

    # Rows
    for r_idx, row in enumerate(rows, start=1):
        row_frame = ctk.CTkFrame(scroll, fg_color="#111827")
        row_frame.grid(row=r_idx, column=0, sticky="ew", pady=2)
        for c_idx, h in enumerate(headers):
            val = row.get(h, "")
            ctk.CTkLabel(row_frame, text=str(val)).grid(
                row=0, column=c_idx, padx=6, pady=4, sticky="w"
            )

    return win
