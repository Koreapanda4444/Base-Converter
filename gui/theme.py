import customtkinter as ctk
def apply_theme():
    try:
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
    except Exception:
        pass
