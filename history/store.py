import os, json, csv
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Iterable

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

    def export_csv(self, path: str, rows: Iterable[HistoryItem] = None):
        rows = list(rows) if rows is not None else self.items
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "expr", "base_from", "base_to", "result"])
            for it in rows:
                w.writerow([it.timestamp, it.expr, it.base_from, it.base_to, it.result])

    def import_csv(self, path: str, mode: str = "append"):
        imported: List[HistoryItem] = []
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            r = csv.reader(f)
            rows = list(r)

        if not rows:
            return

        header_idx = 0
        header = [c.lower() for c in rows[0]]
        has_header = set(("timestamp", "expr", "base_from", "base_to", "result")).issubset(set(header))
        if has_header:
            header_idx = 1

        def row_to_item(cols):
            if has_header:
                m = {header[i]: cols[i] for i in range(min(len(header), len(cols)))}
                ts = m.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                expr = m.get("expr", "")
                bfrom = int(m.get("base_from", "10"))
                bto = int(m.get("base_to", "10"))
                res = m.get("result", "")
            else:
                ts = cols[0] if len(cols) > 0 else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                expr = cols[1] if len(cols) > 1 else ""
                bfrom = int(cols[2]) if len(cols) > 2 else 10
                bto = int(cols[3]) if len(cols) > 3 else 10
                res = cols[4] if len(cols) > 4 else ""
            return HistoryItem(expr=expr, base_from=bfrom, base_to=bto, result=res, timestamp=ts)

        for row in rows[header_idx:]:
            if not row:
                continue
            try:
                imported.append(row_to_item(row))
            except Exception:
                continue

        if mode == "replace":
            self.items = imported[:MAX_ITEMS]
        else:
            self.items = list(reversed(imported)) + self.items
            self.items = self.items[:MAX_ITEMS]

        self._save()
