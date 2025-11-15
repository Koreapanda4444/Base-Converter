import os, json, csv
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Iterable

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
MAX_ITEMS = 300

@dataclass
class HistoryItem:
    expr: str
    base_from: int
    base_to: int
    result: str
    timestamp: str
    favorite: bool = False

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

    def toggle_favorite(self, idx: int):
        if 0 <= idx < len(self.items):
            self.items[idx].favorite = not self.items[idx].favorite
            self._save()

    def remove_item(self, item: HistoryItem):
        self.items = [
            it for it in self.items
            if not (
                it.expr == item.expr and
                it.base_from == item.base_from and
                it.base_to == item.base_to and
                it.result == item.result and
                it.timestamp == item.timestamp
            )
        ]
        self._save()

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
        data = self.items

        if q:
            if q in {"fav", "star"}:
                data = [i for i in data if i.favorite]
            else:
                data = [i for i in data if q in i.expr.lower() or q in i.result.lower()]

        reverse = "desc" in sort_mode

        if "time" in sort_mode:
            key = lambda x: x.timestamp
        elif "expr" in sort_mode:
            key = lambda x: x.expr.lower()
        elif "bfrom" in sort_mode:
            key = lambda x: x.base_from
        elif "bto" in sort_mode:
            key = lambda x: x.base_to
        elif "fav" in sort_mode:
            key = lambda x: (not x.favorite, x.timestamp)
        else:
            key = lambda x: x.result.lower()

        return sorted(data, key=key, reverse=reverse)

    def export_csv(self, path: str, rows: Iterable[HistoryItem] = None):
        rows = list(rows) if rows is not None else self.items
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "expr", "base_from", "base_to", "result", "favorite"])
            for it in rows:
                w.writerow([
                    it.timestamp, it.expr, it.base_from, it.base_to,
                    it.result, int(it.favorite)
                ])

    def import_csv(self, path: str, mode: str = "append"):
        imported: List[HistoryItem] = []
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))

        if not rows:
            return

        header = [c.lower() for c in rows[0]]
        has_header = set(("timestamp", "expr", "base_from", "base_to", "result")).issubset(header)
        start = 1 if has_header else 0

        for row in rows[start:]:
            if not row:
                continue
            try:
                if has_header:
                    m = {header[i]: row[i] for i in range(min(len(header), len(row)))}
                    it = HistoryItem(
                        timestamp=m.get("timestamp", ""),
                        expr=m.get("expr", ""),
                        base_from=int(m.get("base_from", "10")),
                        base_to=int(m.get("base_to", "10")),
                        result=m.get("result", ""),
                        favorite=bool(int(m.get("favorite", "0"))) if "favorite" in m else False,
                    )
                else:
                    it = HistoryItem(
                        timestamp=row[0],
                        expr=row[1],
                        base_from=int(row[2]),
                        base_to=int(row[3]),
                        result=row[4],
                        favorite=bool(int(row[5])) if len(row) > 5 else False,
                    )
                imported.append(it)
            except Exception:
                continue

        if mode == "replace":
            self.items = imported[:MAX_ITEMS]
        else:
            self.items = list(reversed(imported)) + self.items
            self.items = self.items[:MAX_ITEMS]

        self._save()

    def export_json(self, path: str, rows: Iterable[HistoryItem] = None):
        rows = list(rows) if rows is not None else self.items
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(i) for i in rows], f, ensure_ascii=False, indent=2)

    def import_json(self, path: str, mode: str = "append"):
        try:
            data = json.loads(open(path, "r", encoding="utf-8").read())
            imported = [HistoryItem(**d) for d in data]
        except Exception:
            return

        if mode == "replace":
            self.items = imported[:MAX_ITEMS]
        else:
            self.items = imported + self.items
            self.items = self.items[:MAX_ITEMS]

        self._save()
