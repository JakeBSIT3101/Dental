import customtkinter as ctk


def init_theme() -> None:
    """Apply a consistent appearance across the app."""
    ctk.set_appearance_mode("System")
    # Base palette will be overridden per-widget for the hero/login card,
    # but this keeps buttons/text aligned with a modern cyan/blue accent.
    ctk.set_default_color_theme("blue")
