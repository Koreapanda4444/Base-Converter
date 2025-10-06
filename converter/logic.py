# gui/ui.py
import re
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox, END, Scrollbar, filedialog

from gui import ui_text as T
from history.store import HistoryStore, HistoryItem
from converter.logic import convert, to_decimal, from_decimal, evaluate_expression

MIN_W, MIN_H = 900, 560
MAX_W, MAX_H = 1600, 1000

ROUND_CHOICES = ["HALF_UP", "HALF_DOWN", "HALF_EVEN", "CEILING", "FLOOR"]
SORT_CHOICES = [
    ("최신순", "time_desc"),
    ("오래된순", "time_asc"),
    ("입력 A→Z", "expr_asc"),
    ("입력 Z→A", "expr_desc"),
    ("결과 A→Z", "result_asc"),
    ("결과 Z→A", "result_desc"),
    ("입력진법 ↑", "bfrom_asc"),
    ("입력진법 ↓", "bfrom_desc"),
    ("출력진법 ↑", "bto_asc"),
    ("출력진법 ↓", "bto_desc"),
]

CASE_CHOICES = ["UPPER", "lower"]
GROUP_CHOICES = ["없음", "4자리"]
SEP_CHOICES = ["공백", "언더스코어(_ )"]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title(T.APP_TITLE)
        self._init_window_size()
        self.hist = HistoryStore()
        self._hist_view = []  # 현재 화면에 표시 중 뷰(검색/정렬 반영본)

        self._build_panes()
        self._style_treeview()
        self._init_hint()

        self.after(100, self._hist_refresh)
        self.ent_input.bind("<Return>", lambda e: self.on_convert())

    # -----------------------------
    def _init_window_size(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        gw, gh = int(sw * 0.6), int(sh * 0.65)
        gw = max(MIN_W, min(gw, MAX_W))
        gh = max(MIN_H, min(gh, MAX_H))
        x, y = (sw - gw) // 2, (sh - gh) // 2
        self.geometry(f"{gw}x{gh}+{x}+{y}")
        self.minsize(MIN_W, MIN_H)

    # -----------------------------
    def _build_panes(self):
        pw = tk.PanedWindow(self, orient="horizontal", sashwidth=8, opaqueresize=True)
        pw.pack(side="top", fill="both", expand=True, padx=12, pady=12)

        self.left = ctk.CTkFrame(pw)
        self.mid = ctk.CTkFrame(pw)
        self.right = ctk.CTkFrame(pw)
        pw.add(self.left, minsize=420)
        pw.add(self.mid, minsize=320)
        pw.add(self.right, minsize=300)

        # LEFT
        self.left.grid_columnconfigure(0, weight=1)

        inp = ctk.CTkFrame(self.left)
        inp.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        inp.grid_columnconfigure(10, weight=1)

        ctk.CTkLabel(inp, text=T.LBL_INPUT).grid(row=0, column=0, sticky="w")
        self.var_input = tk.StringVar(value="")
        self.ent_input = ctk.CTkEntry(inp, textvariable=self.var_input, placeholder_text="예: 1011.01 또는 (A.F + 10)")
        self.ent_input.grid(row=1, column=0, columnspan=11, sticky="ew", pady=(2, 8))

        ctk.CTkLabel(inp, text=T.LBL_FROM).grid(row=2, column=0, sticky="w")
        self.var_from = tk.StringVar(value="10")
        self.cmb_from = ctk.CTkComboBox(inp, values=T.BASES, variable=self.var_from, width=90)
        self.cmb_from.grid(row=3, column=0, sticky="w")

        ctk.CTkLabel(inp, text=T.LBL_TO).grid(row=2, column=1, sticky="w")
        self.var_to = tk.StringVar(value="2")
        self.cmb_to = ctk.CTkComboBox(inp, values=T.BASES, variable=self.var_to, width=90)
        self.cmb_to.grid(row=3, column=1, sticky="w", padx=(6, 0))

        ctk.CTkLabel(inp, text="정밀도").grid(row=2, column=2, sticky="w")
        self.var_prec = tk.IntVar(value=12)
        self.ent_prec = ctk.CTkEntry(inp, textvariable=self.var_prec, width=60)
        self.ent_prec.grid(row=3, column=2, sticky="w", padx=(2, 8))

        ctk.CTkLabel(inp, text="반올림").grid(row=2, column=3, sticky="w")
        self.var_round = tk.StringVar(value="HALF_UP")
        self.cmb_round = ctk.CTkComboBox(inp, values=ROUND_CHOICES, variable=self.var_round, width=120)
        self.cmb_round.grid(row=3, column=3, sticky="w", padx=(2, 8))

        # ---- 출력 서식 옵션 ----
        fmt_fr = ctk.CTkFrame(self.left)
        fmt_fr.grid(row=4, column=0, sticky="ew", pady=(2, 8))
        fmt_fr.grid_columnconfigure(10, weight=1)

        ctk.CTkLabel(fmt_fr, text="서식").grid(row=0, column=0, sticky="w", padx=(0,6))

        # 대/소문자
        ctk.CTkLabel(fmt_fr, text="문자").grid(row=0, column=1, sticky="w")
        self.var_case = tk.StringVar(value=CASE_CHOICES[0])
        self.cmb_case = ctk.CTkComboBox(fmt_fr, values=CASE_CHOICES, variable=self.var_case, width=85)
        self.cmb_case.grid(row=0, column=2, sticky="w", padx=(2, 10))

        # 그룹
        ctk.CTkLabel(fmt_fr, text="그룹").grid(row=0, column=3, sticky="w")
        self.var_group = tk.StringVar(value=GROUP_CHOICES[0])
        self.cmb_group = ctk.CTkComboBox(fmt_fr, values=GROUP_CHOICES, variable=self.var_group, width=85)
        self.cmb_group.grid(row=0, column=4, sticky="w", padx=(2, 10))

        # 구분자
        ctk.CTkLabel(fmt_fr, text="구분자").grid(row=0, column=5, sticky="w")
        self.var_sep = tk.StringVar(value=SEP_CHOICES[0])
        self.cmb_sep = ctk.CTkComboBox(fmt_fr, values=SEP_CHOICES, variable=self.var_sep, width=120)
        self.cmb_sep.grid(row=0, column=6, sticky="w", padx=(2, 10))

        # 접두어
        self.var_prefix = tk.BooleanVar(value=False)
        self.chk_prefix = ctk.CTkCheckBox(fmt_fr, text="접두어(0x/0b/0o)", variable=self.var_prefix)
        self.chk_prefix.grid(row=0, column=7, sticky="w")

        # 버튼들
        self.btn_convert = ctk.CTkButton(inp, text=T.BTN_CONVERT, command=self.on_convert, width=110)
        self.btn_convert.grid(row=3, column=4, padx=(12, 6))
        self.btn_swap = ctk.CTkButton(inp, text=T.BTN_SWAP, command=self.on_swap, width=70)
        self.btn_swap.grid(row=3, column=5, padx=6)
        self.btn_clear = ctk.CTkButton(inp, text=T.BTN_CLEAR, command=self.on_clear, width=80)
        self.btn_clear.grid(row=3, column=6, padx=6)

        # 결과 영역
        ctk.CTkLabel(self.left, text=T.LBL_RESULT).grid(row=5, column=0, sticky="w")
        res_row = ctk.CTkFrame(self.left)
        res_row.grid(row=6, column=0, sticky="ew", pady=(2, 6))
        res_row.grid_columnconfigure(0, weight=1)
        self.var_result = tk.StringVar(value="")
        self.ent_result = ctk.CTkEntry(res_row, textvariable=self.var_result, state="readonly")
        self.ent_result.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(res_row, text=T.BTN_COPY, width=60,
                      command=lambda: self._copy_to_clip(self.ent_result.get())).grid(row=0, column=1, padx=(6, 0))

        # 요약 영역 (2,8,10,16진)
        ctk.CTkLabel(self.left, text=T.LBL_SUMMARY).grid(row=7, column=0, sticky="w", pady=(6, 2))
        self.sum2 = self._mk_sum_row(self.left, 8, "2진")
        self.sum8 = self._mk_sum_row(self.left, 9, "8진")
        self.sum10 = self._mk_sum_row(self.left, 10, "10진")
        self.sum16 = self._mk_sum_row(self.left, 11, "16진")

        # MID
        self.mid.grid_columnconfigure(0, weight=1)
        self.mid.grid_rowconfigure(1, weight=1)
        self.lbl_steps = ctk.CTkLabel(self.mid, text=T.LBL_STEPS)
        self.lbl_steps.grid(row=0, column=0, sticky="w")
        self.txt_steps = ctk.CTkTextbox(self.mid, wrap="word")
        self.txt_steps.grid(row=1, column=0, sticky="nsew")

        # RIGHT (검색/정렬/컨트롤/테이블) — 이전 그대로
        self.right.grid_columnconfigure(0, weight=1)
        self.right.grid_rowconfigure(3, weight=1)

        head = ctk.CTkFrame(self.right, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=(0, 0), pady=(0, 6))
        head.grid_columnconfigure(0, weight=1)

        search_wrap = ctk.CTkFrame(head, fg_color="transparent")
        search_wrap.pack(side="top", fill="x")
        ctk.CTkLabel(search_wrap, text="검색").pack(side="left", padx=(0, 6))
        self.var_search = tk.StringVar(value="")
        ent_search = ctk.CTkEntry(search_wrap, textvariable=self.var_search, width=160, placeholder_text="입력/결과로 검색")
        ent_search.pack(side="left")
        ent_search.bind("<KeyRelease>", lambda e: self._hist_refresh())

        ctk.CTkLabel(search_wrap, text="정렬").pack(side="left", padx=(12, 6))
        self.var_sort = tk.StringVar(value=SORT_CHOICES[0][0])
        self.cmb_sort = ctk.CTkComboBox(search_wrap, values=[x[0] for x in SORT_CHOICES], variable=self.var_sort, width=120)
        self.cmb_sort.pack(side="left")
        self.cmb_sort.bind("<<ComboboxSelected>>", lambda e: self._hist_refresh())

        control_wrap = ctk.CTkFrame(self.right, fg_color="transparent")
        control_wrap.grid(row=1, column=0, sticky="ew", padx=(0, 0), pady=(0, 4))
        ctk.CTkButton(control_wrap, text="선택삭제", width=80, command=self.on_hist_delete).pack(side="left", padx=(0,6))
        ctk.CTkButton(control_wrap, text="전체삭제", width=80, command=self.on_hist_clear).pack(side="left", padx=(0,6))
        ctk.CTkButton(control_wrap, text="CSV로 내보내기", width=120, command=self.on_hist_export).pack(side="right")
        ctk.CTkButton(control_wrap, text="CSV 가져오기", width=110, command=self.on_hist_import).pack(side="right", padx=(0,6))

        wrap = ctk.CTkFrame(self.right)
        wrap.grid(row=2, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(wrap, columns=("expr", "bases", "result"), show="headings", selectmode="browse")
        self.tree.heading("expr", text="입력")
        self.tree.heading("bases", text="진법")
        self.tree.heading("result", text="결과")
        self.tree.column("expr", width=220, anchor="w")
        self.tree.column("bases", width=80, anchor="center")
        self.tree.column("result", width=170, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        sb = Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", self.on_hist_load)
        self.tree.bind("<Return>", self.on_hist_load)

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(side="bottom", fill="x", padx=12, pady=(0, 6))

    # -----------------------------
    def _mk_sum_row(self, parent, r, label):
        fr = ctk.CTkFrame(parent)
        fr.grid(row=r, column=0, sticky="ew", pady=2)
        fr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fr, text=label, width=40).grid(row=0, column=0, sticky="w")
        entry = ctk.CTkEntry(fr, state="readonly")
        entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(fr, text=T.BTN_COPY, width=60,
                      command=lambda e=entry: self._copy_to_clip(e.get())).grid(row=0, column=2, padx=(6, 0))
        return entry

    def _style_treeview(self):
        style = ttk.Style()
        try:
            style.theme_use("default")
        except Exception:
            pass

        mode = ctk.get_appearance_mode()
        dark = (mode.lower() == "dark")

        bg = "#1E1E1E" if dark else "#F2F2F2"
        fg = "#FFFFFF" if dark else "#000000"
        sel_bg = "#2D6CDF" if dark else "#CDE1FF"
        sel_fg = "#FFFFFF" if dark else "#000000"
        head_bg = "#2A2A2A" if dark else "#E6E6E6"
        head_fg = "#FFFFFF" if dark else "#000000"
        border = "#333333" if dark else "#C0C0C0"

        style.configure(
            "Treeview",
            background=bg,
            fieldbackground=bg,
            foreground=fg,
            rowheight=24,
            bordercolor=border,
            borderwidth=0
        )
        style.map(
            "Treeview",
            background=[("selected", sel_bg)],
            foreground=[("selected", sel_fg)]
        )
        style.configure(
            "Treeview.Heading",
            background=head_bg,
            foreground=head_fg,
            relief="flat"
        )
        style.map("Treeview.Heading",
                  background=[("active", head_bg)],
                  foreground=[("active", head_fg)])

    def _init_hint(self):
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        self.txt_steps.insert("end", T.HINT)
        self.txt_steps.configure(state="disabled")

    # -----------------------------
    def _hist_refresh(self):
        label = self.var_sort.get()
        sort_mode = next((code for text, code in SORT_CHOICES if text == label), "time_desc")
        query = self.var_search.get()

        self._hist_view = self.hist.list_items(query=query, sort_mode=sort_mode)

        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for idx, item in enumerate(self._hist_view):
            bases = f"{item.base_from}→{item.base_to}"
            self.tree.insert("", "end", iid=str(idx), values=(item.expr, bases, item.result))

    # -----------------------------
    def _copy_to_clip(self, text: str):
        if not text:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status.configure(text="클립보드에 복사됨")
        except Exception:
            pass

    def on_swap(self):
        f, t = self.var_from.get(), self.var_to.get()
        self.var_from.set(t)
        self.var_to.set(f)

    def on_clear(self):
        self.var_input.set("")
        self.var_result.set("")
        for e in (self.sum2, self.sum8, self.sum10, self.sum16):
            e.configure(state="normal")
            e.delete(0, END)
            e.configure(state="readonly")
        self._init_hint()
        self.status.configure(text="")

    # 더블클릭/Enter: 불러오고 결과 자동복사
    def on_hist_load(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if not (0 <= idx < len(self._hist_view)):
            return
        item = self._hist_view[idx]
        self.var_input.set(item.expr)
        self.var_from.set(str(item.base_from))
        self.var_to.set(str(item.base_to))
        self._recompute(add_history=False)
        self._copy_to_clip(self.var_result.get())
        self.status.configure(text="불러오기 + 결과 복사 완료")

    def on_hist_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("알림", "삭제할 항목을 선택하세요.")
            return
        idx = int(sel[0])
        if not (0 <= idx < len(self._hist_view)):
            return
        item = self._hist_view[idx]
        self.hist.remove_item(item)
        self._hist_refresh()
        self.status.configure(text="선택 항목 삭제됨")

    def on_hist_clear(self):
        if messagebox.askyesno("확인", "히스토리를 모두 삭제할까요?"):
            self.hist.clear()
            self._hist_refresh()
            self.status.configure(text="히스토리 초기화됨")

    def on_hist_export(self):
        path = filedialog.asksaveasfilename(
            title="CSV로 내보내기",
            defaultextension=".csv",
            filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
            initialfile="history.csv"
        )
        if not path:
            return
        try:
            self.hist.export_csv(path, self._hist_view)
            messagebox.showinfo("완료", "히스토리를 CSV로 저장했습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"CSV 저장에 실패했습니다.\n{e}")

    def on_hist_import(self):
        path = filedialog.askopenfilename(
            title="CSV 가져오기",
            filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")]
        )
        if not path:
            return

        ans = messagebox.askyesnocancel("가져오기 모드 선택",
                                        "예: 기존 히스토리에 추가(append)\n아니오: 기존 히스토리를 대체(replace)\n취소: 중단")
        if ans is None:
            return
        mode = "append" if ans else "replace"

        try:
            self.hist.import_csv(path, mode=mode)
            self._hist_refresh()
            msg = "추가 완료" if mode == "append" else "대체 완료"
            messagebox.showinfo("완료", f"CSV {msg}되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"CSV 가져오기에 실패했습니다.\n{e}")

    def on_convert(self):
        self._recompute(add_history=True)

    # -----------------------------
    def _current_format(self):
        # letter case
        letter_case = "upper" if self.var_case.get() == "UPPER" else "lower"
        # group size
        group_size = 0 if self.var_group.get() == "없음" else 4
        # separator
        sep = " " if self.var_sep.get().startswith("공백") else "_"
        use_prefix = bool(self.var_prefix.get())
        return {
            "letter_case": letter_case,
            "group_size": group_size,
            "group_sep": sep,
            "prefix": use_prefix
        }

    def _recompute(self, add_history: bool):
        expr = self.var_input.get().strip()
        if not expr:
            messagebox.showerror("오류", "입력 값이 비어 있습니다.")
            return
        try:
            base_from = int(self.var_from.get())
            base_to = int(self.var_to.get())
            precision = int(self.var_prec.get())
            round_mode = self.var_round.get().strip() or "HALF_UP"
        except Exception:
            messagebox.showerror("오류", "진법 또는 정밀도/반올림 설정이 잘못되었습니다.")
            return

        fmt = self._current_format()

        try:
            out, steps = convert(expr, base_from, base_to, precision=precision, round_mode_str=round_mode, fmt=fmt)
        except Exception as e:
            messagebox.showerror("변환 실패", f"{T.ERR_INVALID}\n\n{e}")
            return

        # 결과
        self.var_result.set(out)
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        for s in steps:
            self.txt_steps.insert("end", s + "\n")
        self.txt_steps.configure(state="disabled")

        # 요약 (2/8/10/16) — 동일 서식 적용
        try:
            # 이미 convert 내부에서 Fraction 평가하므로 여기선 expr를 재해석할 필요 없음.
            # 요약은 현재 결과(10진 Fraction)를 재활용하고 싶지만,
            # 간단히 base_from 기준으로 재계산 경로 사용.
            if any(c in expr for c in "+-*/()%^"):
                dec, _ = evaluate_expression(expr, base_from, precision=precision, round_mode=round_mode)
            else:
                dec, _ = evaluate_expression(expr, base_from, precision=precision, round_mode=round_mode)

            b2, _ = from_decimal(dec, 2, precision, fmt=fmt)
            b8, _ = from_decimal(dec, 8, precision, fmt=fmt)
            b10, _ = from_decimal(dec, 10, precision, fmt=fmt)
            b16, _ = from_decimal(dec, 16, precision, fmt=fmt)
            for entry, val in ((self.sum2, b2), (self.sum8, b8), (self.sum10, b10), (self.sum16, b16)):
                entry.configure(state="normal")
                entry.delete(0, END)
                entry.insert(0, val)
                entry.configure(state="readonly")
        except Exception:
            pass

        if add_history:
            self.hist.add(expr, base_from, base_to, out)
            self._hist_refresh()


def run():
    app = App()
    app.mainloop()
