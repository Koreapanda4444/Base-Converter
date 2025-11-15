import os, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTABLE = (ROOT / "portable.flag").exists()

if PORTABLE:
    CONFIG_DIR = ROOT / "data"
else:
    CONFIG_DIR = Path(os.getenv("APPDATA", Path.home())) / "BaseConverter"

CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "precision": 12,
    "round_mode": "HALF_UP",
    "sig": 0,
    "sci": False
}

def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            d = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            x = DEFAULT_CONFIG.copy()
            x.update(d)
            return x
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(data: dict):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass