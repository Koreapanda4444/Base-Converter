from __future__ import annotations
import json, os
from pathlib import Path
from fractions import Fraction

VAR_PATH = Path(os.getenv("APPDATA", Path.home())) / "BaseConverter" / "vars.json"

def _load() -> dict:
    try:
        if VAR_PATH.exists():
            return json.loads(VAR_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _save(d: dict):
    try:
        VAR_PATH.parent.mkdir(parents=True, exist_ok=True)
        VAR_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def get_vars() -> dict:
    return _load()

def set_var(name: str, value: Fraction):
    d = _load()
    d[name] = {"num": value.numerator, "den": value.denominator}
    _save(d)

def resolve(name: str):
    d = _load()
    v = d.get(name)
    if not v:
        raise ValueError(f"정의되지 않은 변수: {name}")
    return Fraction(int(v["num"]), int(v["den"]))
