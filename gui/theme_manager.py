import os, json
from pathlib import Path
import customtkinter as ctk

ASSETS_PATH = Path(__file__).resolve().parent.parent / "assets"
THEME_PATH = ASSETS_PATH / "theme.json"

DEFAULT_THEME = {
    "CTk": {
        "fg_color": ["#FFFFFF", "#1E1E1E"],
        "text_color": ["#000000", "#FFFFFF"],
        "button_color": ["#007ACC", "#3B82F6"],
        "button_hover_color": ["#005A9E", "#2563EB"]
    }
}


def load_theme():
    if THEME_PATH.exists():
        try:
            with open(THEME_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_THEME.copy()
    return DEFAULT_THEME.copy()


def save_theme(data: dict):
    THEME_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(THEME_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def apply_theme(theme: dict):
    """customtkinter에 테마 적용"""
    temp_path = ASSETS_PATH / "_temp_theme.json"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=2)
    ctk.set_default_color_theme(str(temp_path))
