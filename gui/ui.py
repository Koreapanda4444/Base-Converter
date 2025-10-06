# gui/ui.py
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, END, Scrollbar, ttk

from gui import ui_text_kr as KR
from gui import ui_text_en as EN
from gui.config_manager import load_config, save_config
from history.store import HistoryStore
from converter.logic import convert, evaluate_expression, to_decimal, from_decimal


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # 설정 불러오기
        self.config_data = load_config()
        self.lang = self.config_data.get("language", "KR")
        self.texts = KR if self.lang == "KR" else EN

        ctk.set_appearance_mode(self.config_data.get("theme", "system"))
        ctk.set_default_color_theme("blue")

        self.title(self.texts.APP_TITLE)
        self.geometry("1000x600")
        self.minsize(900, 560)

        self.hist = HistoryStore()
        self._hist_view = []

        self._build_ui()
        self._hist_refresh()

    # -----------------------------
    # UI 빌드
    # -----------------------------
    def _build_ui(self):
        topbar = ctk.CTkFrame(self)
        topbar.pack(fill="x", padx=10, pady=6)

        # 언어 토글
        self.lang_btn = ctk.CTkSegmentedButton(topbar, values=["KR", "EN"], command=self._on_lang_change)
        self.lang_btn.set(self.lang)
        self.lang_btn.pack(side="right", padx=(0, 10))

        # 정밀도 설정
        ctk.CTkLabel(topbar, text="정밀도").pack(side="left")
        self.prec_var = tk.IntVar(value=self.config_data.get("precision", 12))
        ctk.CTkEntry(topbar, textvariable=self.prec_var, width=50).pack(side="left", padx=6)

        # 반올림 모드
        ctk.CTkLabel(topbar, text="반올림").pack(side="left")
        self.round_var = tk.StringVar(value=self.config_data.get("round_mode", "HALF_UP"))
        ctk.CTkComboBox(topbar, values=["HALF_UP", "HALF_DOWN", "HALF_EVEN", "CEILING", "FLOOR"],
                        variable=self.round_var, width=120).pack(side="left", padx=6)

        # 변환 입력부
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(frame, text=self.texts.LBL_INPUT).grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar(value="")
        self.ent_input = ctk.CTkEntry(frame, textvariable=self.input_var, placeholder_text="예: 1011 + A.F")
        self.ent_input.grid(row=0, column=1, sticky="ew", pady=4)

        # 진법 선택
        ctk.CTkLabel(frame, text=self.texts.LBL_FROM).grid(row=1, column=0, sticky="w")
        self.base_from = tk.StringVar(value="10")
        self.cmb_from = ctk.CTkComboBox(frame, values=[str(i) for i in range(2, 37)], variable=self.base_from, width=80)
        self.cmb_from.grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(frame, text=self.texts.LBL_TO).grid(row=1, column=1, sticky="e", padx=(0, 120))
        self.base_to = tk.StringVar(value="2")
        self.cmb_to = ctk.CTkComboBox(frame, values=[str(i) for i in range(2, 37)], variable=self.base_to, width=80)
        self.cmb_to.place(relx=0.9, rely=0.22)

        # 결과
        ctk.CTkLabel(frame, text=self.texts.LBL_RESULT).grid(row=2, column=0, sticky="nw")
        self.result_var = tk.StringVar(value="")
        self.ent_result = ctk.CTkEntry(frame, textvariable=self.result_var, state="readonly")
        self.ent_result.grid(row=2, column=1, sticky="ew", pady=(0, 6))

        ctk.CTkButton(frame, text=self.texts.BTN_CONVERT, command=self.on_convert).grid(row=3, column=1, sticky="e", pady=(6, 0))

        # 히스토리
        self.tree = ttk.Treeview(frame, columns=("expr", "result"), show="headings")
        self.tree.heading("expr", text="입력")
        self.tree.heading("result", text="결과")
        self.tree.grid(row=4, column=0, columnspan=2, sticky="nsew")
        self.tree.bind("<Double-1>", self.on_hist_load)
        sb = Scrollbar(frame, command=self.tree.yview)
        sb.grid(row=4, column=2, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

    # -----------------------------
    # 이벤트
    # -----------------------------
    def on_convert(self):
        expr = self.input_var.get().strip()
        if not expr:
            messagebox.showerror("오류", "입력값이 없습니다.")
            return
        try:
            base_from = int(self.base_from.get())
            base_to = int(self.base_to.get())
            prec = int(self.prec_var.get())
            round_mode = self.round_var.get()
            result, steps = convert(expr, base_from, base_to, precision=prec, round_mode_str=round_mode)
            self.result_var.set(result)
            self.hist.add(expr, base_from, base_to, result)
            self._hist_refresh()
            self._save_user_config()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_hist_load(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < len(self._hist_view):
            item = self._hist_view[idx]
            self.input_var.set(item.expr)
            self.base_from.set(str(item.base_from))
            self.base_to.set(str(item.base_to))
            self.on_convert()

    def _hist_refresh(self):
        self._hist_view = self.hist.list_items()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self._hist_view):
            self.tree.insert("", "end", iid=str(idx), values=(item.expr, item.result))

    def _on_lang_change(self, value):
        """언어 토글 시 텍스트 전환"""
        self.lang = value
        self.texts = KR if value == "KR" else EN
        self.title(self.texts.APP_TITLE)
        save_config({"language": self.lang})

    def _save_user_config(self):
        data = {
            "language": self.lang,
            "theme": "system",
            "precision": self.prec_var.get(),
            "round_mode": self.round_var.get(),
        }
        save_config(data)


def run():
    app = App()
    app.mainloop()
