from dataclasses import dataclass, asdict
from typing import List, Optional
import json, os


@dataclass
class HistItem:
    expr: str
    base_from: int
    base_to: int
    result: str

    def __str__(self):
        return f"[{self.base_from}→{self.base_to}] {self.expr} = {self.result}"


class HistoryStore:
    """히스토리: 메모리 + JSON 자동 저장/불러오기"""
    def __init__(self, file_path: str = "history.json"):
        self.items: List[HistItem] = []
        self.file_path = file_path
        self.load()

    def add(self, expr: str, base_from: int, base_to: int, result: str):
        self.items.insert(0, HistItem(expr, base_from, base_to, result))
        self.save()

    def remove(self, idx: int):
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self.save()

    def clear(self):
        self.items.clear()
        self.save()

    def get(self, idx: int) -> Optional[HistItem]:
        if 0 <= idx < len(self.items):
            return self.items[idx]
        return None

    def list_texts(self):
        return [str(item) for item in self.items]

    def save(self):
        try:
            data = [asdict(it) for it in self.items]
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.items = [HistItem(**it) for it in data]
            except Exception:
                self.items = []
