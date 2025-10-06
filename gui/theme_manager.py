import json
import os
from pathlib import Path
import customtkinter as ctk

ROOT = Path(__file__).resolve().parents[1]
ASSETS_PATH = ROOT / "assets"
THEME_PATH = ASSETS_PATH / "theme.json"

def load_theme():
    try:
        if THEME_PATH.exists():
            return json.loads(THEME_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _is_valid_theme(t: dict) -> bool:
    return isinstance(t, dict) and "CTkFrame" in t

def apply_theme(theme: dict | None):
    try:
        if _is_valid_theme(theme or {}):
            temp_path = ASSETS_PATH / "_temp_theme.json"
            temp_path.write_text(json.dumps(theme, indent=2, ensure_ascii=False), encoding="utf-8")
            ctk.set_default_color_theme(str(temp_path))
        else:
            ctk.set_default_color_theme("blue")
    except Exception:
        ctk.set_default_color_theme("blue")
