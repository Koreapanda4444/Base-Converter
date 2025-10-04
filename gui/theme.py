from gui.theme_manager import ThemeConfig, load_theme, save_theme, apply_theme, make_font

def init_theme():
    cfg = load_theme()
    apply_theme(cfg)
    return cfg
