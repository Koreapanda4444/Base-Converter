import customtkinter as ctk
from gui.config_manager import load_config, save_config

def apply_theme():
    cfg = load_config()
    mode = cfg.get("theme", "system")
    ctk.set_appearance_mode(mode)

def set_theme(mode: str):
    cfg = load_config()
    cfg["theme"] = mode
    save_config(cfg)
    apply_theme()
