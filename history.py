from dataclasses import dataclass

@dataclass
class HistItem:
    expr: str
    base_from: int
    base_to: int
    result: str

    def __str__(self):
        return f"[{self.base_from}→{self.base_to}] {self.expr} = {self.result}"


class HistoryStore:
    def __init__(self):
        self.items = []

    def add(self, expr, base_from, base_to, result):
        # 맨 앞에 삽입 (최근 기록이 위로 올라오도록)
        self.items.insert(0, HistItem(expr, base_from, base_to, result))

    def list_texts(self):
        # 전체 기록을 문자열 리스트로 반환
        return [str(item) for item in self.items]

    def get(self, idx: int):
        if 0 <= idx < len(self.items):
            return self.items[idx]
        return None
