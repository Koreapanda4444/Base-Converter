import os, json
from pathlib import Path

CONFIG_DIR = Path(os.getenv("APPDATA", Path.home())) / "BaseConverter"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "language": "KR",
    "theme": "system",
    "precision": 12,
    "round_mode": "HALF_UP",
    "format_case": "UPPER",
    "format_group": "none",
    "format_sep": " ",
    "format_prefix": False,
}


def load_config() -> dict:
    """환경설정 JSON 로드 (없으면 기본값 반환)"""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                DEFAULT_CONFIG.update(data)
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()


def save_config(data: dict):
    """환경설정 JSON 저장"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[WARN] 설정 저장 실패:", e)
