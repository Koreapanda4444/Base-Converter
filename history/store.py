import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
MAX_ITEMS = 100  # 최대 100개까지만 저장


@dataclass
class HistoryItem:
    expr: str
    base_from: int
    base_to: int
    result: str
    timestamp: str


class HistoryStore:
    def __init__(self):
        self.items: list[HistoryItem] = []
        self._load()

    # -----------------------------
    # 🔹 히스토리 추가 및 자동 저장
    # -----------------------------
    def add(self, expr: str, base_from: int, base_to: int, result: str):
        """히스토리에 새 기록 추가"""
        item = HistoryItem(
            expr=expr.strip(),
            base_from=base_from,
            base_to=base_to,
            result=result.strip(),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.items.insert(0, item)  # 최신 항목을 맨 앞에
        if len(self.items) > MAX_ITEMS:
            self.items = self.items[:MAX_ITEMS]
        self._save()

    # -----------------------------
    # 🔹 히스토리 파일 저장
    # -----------------------------
    def _save(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([asdict(i) for i in self.items], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[히스토리 저장 실패] {e}")

    # -----------------------------
    # 🔹 히스토리 불러오기
    # -----------------------------
    def _load(self):
        if not os.path.exists(HISTORY_FILE):
            self.items = []
            return
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.items = [HistoryItem(**d) for d in data if isinstance(d, dict)]
        except Exception as e:
            print(f"[히스토리 로드 실패, 초기화] {e}")
            self.items = []
            self._save()

    # -----------------------------
    # 🔹 인덱스로 항목 가져오기
    # -----------------------------
    def get(self, idx: int) -> HistoryItem | None:
        if 0 <= idx < len(self.items):
            return self.items[idx]
        return None

    # -----------------------------
    # 🔹 모든 항목 초기화
    # -----------------------------
    def clear(self):
        self.items.clear()
        self._save()
