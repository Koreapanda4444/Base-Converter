import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
MAX_ITEMS = 100  # 최대 100개까지만 저장


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

    # -----------------------------
    # 🔹 히스토리 추가 및 자동 저장
    # -----------------------------
    def add(self, expr: str, base_from: int, base_to: int, result: str):
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
    # 🔹 인덱스로 항목 가져오기 (원본 리스트 기준)
    # -----------------------------
    def get(self, idx: int) -> Optional[HistoryItem]:
        if 0 <= idx < len(self.items):
            return self.items[idx]
        return None

    # -----------------------------
    # 🔹 검색/정렬 지원 리스트 반환 (UI용)
    #     - query: expr/result에 부분일치(대소문자 무시)
    #     - sort_mode:
    #         time_desc, time_asc,
    #         expr_asc, expr_desc,
    #         result_asc, result_desc,
    #         bfrom_asc, bfrom_desc,
    #         bto_asc, bto_desc
    # -----------------------------
    def list_items(self, query: str = "", sort_mode: str = "time_desc") -> List[HistoryItem]:
        q = (query or "").strip().lower()
        if q:
            filtered = [
                it for it in self.items
                if (q in it.expr.lower()) or (q in it.result.lower())
            ]
        else:
            filtered = list(self.items)

        def time_key(it: HistoryItem):
            # 안전 파싱
            try:
                return datetime.strptime(it.timestamp, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return datetime.min

        sort_map = {
            "time_desc":  (lambda it: time_key(it), True),
            "time_asc":   (lambda it: time_key(it), False),
            "expr_asc":   (lambda it: it.expr.lower(), False),
            "expr_desc":  (lambda it: it.expr.lower(), True),
            "result_asc": (lambda it: it.result.lower(), False),
            "result_desc":(lambda it: it.result.lower(), True),
            "bfrom_asc":  (lambda it: it.base_from, False),
            "bfrom_desc": (lambda it: it.base_from, True),
            "bto_asc":    (lambda it: it.base_to, False),
            "bto_desc":   (lambda it: it.base_to, True),
        }
        keyfunc, rev = sort_map.get(sort_mode, sort_map["time_desc"])
        filtered.sort(key=keyfunc, reverse=rev)
        return filtered

    # -----------------------------
    # 🔹 모든 항목 초기화
    # -----------------------------
    def clear(self):
        self.items.clear()
        self._save()
