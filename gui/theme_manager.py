import json, os, customtkinter as ctk

THEME_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "theme.json")
DEFAULT_CONFIG = {
    "mode": "system",
    "accent": "blue",
    "font_family": "Pretendard",
    "font_size": 13
}

class ThemeConfig(dict):
    @property
    def mode(self): return self.get("mode", "system")
    @property
    def accent(self): return self.get("accent", "blue")
    @property
    def font_family(self): return self.get("font_family", "Pretendard")
    @property
    def font_size(self): return int(self.get("font_size", 13))

def load_theme():
    if not os.path.exists(THEME_FILE):
        return ThemeConfig(DEFAULT_CONFIG.copy())
    try:
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = DEFAULT_CONFIG.copy()
        cfg.update({k: data[k] for k in DEFAULT_CONFIG if k in data})
        return ThemeConfig(cfg)
    except Exception:
        return ThemeConfig(DEFAULT_CONFIG.copy())

def save_theme(cfg: ThemeConfig):
    os.makedirs(os.path.dirname(THEME_FILE), exist_ok=True)
    with open(THEME_FILE, "w", encoding="utf-8") as f:
        json.dump(dict(cfg), f, ensure_ascii=False, indent=2)

def apply_theme(cfg: ThemeConfig):
    ctk.set_appearance_mode(cfg.mode)
    ctk.set_default_color_theme(cfg.accent)

def make_font(cfg: ThemeConfig):
    return ctk.CTkFont(family=cfg.font_family, size=cfg.font_size)
