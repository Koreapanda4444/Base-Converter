# history/store.py
import os, json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
MAX_ITEMS = 100

@dataclass
class HistoryItem:
    expr: str
    base_from: int
    base_to: int
    result: str
    timestamp: str  # "YYYY-MM-DD HH:MM:SS"

class HistoryStore:
    def __init__(self):
        self.items: List[HistoryItem] = []
        self._load()

    def add(self, expr, base_from, base_to, result):
        item = HistoryItem(
            expr=str(expr).strip(),
            base_from=int(base_from),
            base_to=int(base_to),
            result=str(result).strip(),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.items.insert(0, item)
        if len(self.items) > MAX_ITEMS:
            self.items = self.items[:MAX_ITEMS]
        self._save()

    # 🔹 선택 삭제
    def remove_item(self, item: HistoryItem):
        self.items = [
            it for it in self.items
            if not (
                it.expr == item.expr
                and it.base_from == item.base_from
                and it.base_to == item.base_to
                and it.result == item.result
                and it.timestamp == item.timestamp
            )
        ]
        self._save()

    # 🔹 전체 삭제
    def clear(self):
        self.items.clear()
        self._save()

    def _save(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([asdict(i) for i in self.items], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load(self):
        if not os.path.exists(HISTORY_FILE):
            return
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.items = [HistoryItem(**d) for d in data if isinstance(d, dict)]
        except Exception:
            self.items = []

    def list_items(self, query: str = "", sort_mode: str = "time_desc") -> List[HistoryItem]:
        q = (query or "").strip().lower()
        data = (
            [i for i in self.items if q in i.expr.lower() or q in i.result.lower()]
            if q else list(self.items)
        )

        reverse = "desc" in sort_mode
        if "time" in sort_mode:
            key = lambda x: x.timestamp
        elif "expr" in sort_mode:
            key = lambda x: x.expr.lower()
        elif "bfrom" in sort_mode:
            key = lambda x: x.base_from
        elif "bto" in sort_mode:
            key = lambda x: x.base_to
        else:
            key = lambda x: x.result.lower()
        return sorted(data, key=key, reverse=reverse)
