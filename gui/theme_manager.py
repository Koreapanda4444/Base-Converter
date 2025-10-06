import json, os
from pathlib import Path
import customtkinter as ctk

ROOT = Path(__file__).resolve().parents[1]
PORTABLE = (ROOT / "portable.flag").exists()

ASSETS_PATH = ROOT / "assets"
if PORTABLE:
    THEME_PATH = ROOT / "data" / "theme.json"
else:
    THEME_PATH = Path(os.getenv("APPDATA", Path.home())) / "BaseConverter" / "theme.json"

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
            return json.loads(THEME_PATH.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_THEME.copy()
    return DEFAULT_THEME.copy()

def save_theme(data: dict):
    THEME_PATH.parent.mkdir(parents=True, exist_ok=True)
    THEME_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def apply_theme(theme: dict):
    temp_path = ASSETS_PATH / "_temp_theme.json"
    temp_path.write_text(json.dumps(theme, indent=2, ensure_ascii=False), encoding="utf-8")
    ctk.set_default_color_theme(str(temp_path))
