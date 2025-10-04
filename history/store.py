# history/store.py
import os, json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
MAX_ITEMS = 100

@dataclass
class HistoryItem:
    expr: str
    base_from: int
    base_to: int
    result: str
    timestamp: str

class HistoryStore:
    def __init__(self):
        self.items: List[HistoryItem] = []
        self._load()

    def add(self, expr, base_from, base_to, result):
        item = HistoryItem(expr, base_from, base_to, result, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.items.insert(0, item)
        if len(self.items) > MAX_ITEMS:
            self.items = self.items[:MAX_ITEMS]
        self._save()

    def _save(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([asdict(i) for i in self.items], f, ensure_ascii=False, indent=2)

    def _load(self):
        if not os.path.exists(HISTORY_FILE):
            return
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.items = [HistoryItem(**d) for d in data]
        except Exception:
            self.items = []

    def list_items(self, query="", sort_mode="time_desc"):
        q = query.lower()
        data = [i for i in self.items if q in i.expr.lower() or q in i.result.lower()]
        reverse = "desc" in sort_mode
        if "time" in sort_mode:
            key = lambda x: x.timestamp
        elif "expr" in sort_mode:
            key = lambda x: x.expr
        else:
            key = lambda x: x.result
        return sorted(data, key=key, reverse=reverse)
