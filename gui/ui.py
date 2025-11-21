import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox

from converter.logic import convert
from history.store import HistoryStore
from gui.config_manager import load_config, save_config

MIN_W, MIN_H = 500, 250

ROUND_CHOICES = ["반올림", "반내림", "짝수", "올림", "버림"]
BASES = [str(i) for i in range(2, 37)]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.title("Base Converter")
        self._init_window_size()
        self.hist = HistoryStore()
        self._hist_view = []
        self._build_ui()
        self._style_treeview()
        self._init_hint()
        self.after(50, self._hist_refresh)
        self.after(120, self._init_sash)  # 초기 분할 높이 설정

    def _init_window_size(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        gw, gh = int(sw * 0.40), int(sh * 0.55)
        gw = max(MIN_W, gw)
        gh = max(MIN_H, gh)
        x, y = (sw - gw)//2, (sh - gh)//2
        self.geometry(f"{gw}x{gh}+{x}+{y}")
        self.minsize(MIN_W, MIN_H)

    def _build_ui(self):
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=8)

        self.var_input = tk.StringVar()
        ctk.CTkLabel(top, text="입력").pack(anchor="w")
        self.ent_input = ctk.CTkEntry(top, textvariable=self.var_input)
        self.ent_input.pack(fill="x")

        opt = ctk.CTkFrame(top)
        opt.pack(fill="x", pady=6)

        ctk.CTkLabel(opt, text="입력진법").grid(row=0, column=0)
        self.var_from = tk.StringVar(value="10")
        ctk.CTkComboBox(opt, values=BASES, variable=self.var_from, width=82).grid(row=1, column=0)

        ctk.CTkLabel(opt, text="출력진법").grid(row=0, column=1, padx=6)
        self.var_to = tk.StringVar(value="2")
        ctk.CTkComboBox(opt, values=BASES, variable=self.var_to, width=82).grid(row=1, column=1, padx=6)

        ctk.CTkLabel(opt, text="정밀도").grid(row=0, column=2)
        self.var_prec = tk.IntVar(value=self.cfg.get("precision", 12))
        ctk.CTkEntry(opt, textvariable=self.var_prec, width=70).grid(row=1, column=2, padx=6)

        ctk.CTkLabel(opt, text="반올림").grid(row=0, column=3)
        self.var_round = tk.StringVar(value=self.cfg.get("round_mode", "HALF_UP"))
        ctk.CTkComboBox(opt, values=ROUND_CHOICES, variable=self.var_round, width=120).grid(row=1, column=3, padx=6)

        ctk.CTkButton(opt, text="변환", command=self.on_convert).grid(row=1, column=4, padx=(14,6))
        ctk.CTkButton(opt, text="초기화", command=self.on_clear).grid(row=1, column=5, padx=6)

        # PanedWindow로 중간(변환 과정)과 기록 영역 분할
        self.pw = tk.PanedWindow(self, orient="vertical", sashwidth=6, sashrelief="flat")
        self.pw.pack(fill="both", expand=True, padx=10, pady=(4,10))

        # 변환 과정 영역 (위 패널)
        mid = ctk.CTkFrame(self.pw)
        ctk.CTkLabel(mid, text="변환 과정").pack(anchor="w", padx=5, pady=(5,2))
        self.txt_steps = ctk.CTkTextbox(mid)  # 높이 고정 안 하고 패널 공간 채움
        self.txt_steps.pack(fill="both", expand=True, padx=5, pady=(0,5))

        # 기록 영역 (아래 패널)
        right = ctk.CTkFrame(self.pw)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(right)
        head.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(head, text="기록").pack(side="left", padx=(0,10))
        ctk.CTkLabel(head, text="검색").pack(side="left")
        self.var_search = tk.StringVar()
        ent_search = ctk.CTkEntry(head, textvariable=self.var_search, width=200)
        ent_search.pack(side="left", padx=4)
        ent_search.bind("<KeyRelease>", lambda _: self._hist_refresh())

        ctk.CTkLabel(head, text="정렬").pack(side="left", padx=(14,4))
        self.var_sort = tk.StringVar(value="최신순")
        cmb = ctk.CTkComboBox(head, values=["최신순","오래된순","입력 A→Z","입력 Z→A"], variable=self.var_sort, width=130)
        cmb.pack(side="left")
        cmb.bind("<<ComboboxSelected>>", lambda _: self._hist_refresh())

        wrap = ctk.CTkFrame(right)
        wrap.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(wrap, columns=("expr","bases","result"), show="headings")
        self.tree.heading("expr", text="입력")
        self.tree.heading("bases", text="진법")
        self.tree.heading("result", text="결과")

        self.tree.column("expr", width=360, minwidth=240, stretch=True)
        self.tree.column("bases", width=110, minwidth=90, anchor="center", stretch=False)
        self.tree.column("result", width=360, minwidth=240, stretch=True)

        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self.on_hist_load)
        self.bind("<Configure>", self._auto_resize_columns)

        # PanedWindow에 두 영역 추가 (최소 높이 지정)
        self.pw.add(mid, minsize=150)
        self.pw.add(right, minsize=160)

    def _init_sash(self):
        # 초기 분할 비율 설정 (중간 영역 45%)
        if hasattr(self, "pw"):
            total = self.pw.winfo_height()
            if total > 0:
                desired_mid = int(total * 0.45)
                self.pw.sash_place(0, 0, desired_mid)

    def _auto_resize_columns(self, event=None):
        total = self.tree.winfo_width()
        bases_w = 110
        padding = 30
        remain = max(100, total - bases_w - padding)
        each = remain // 2
        self.tree.column("expr", width=each)
        self.tree.column("result", width=each)

    def _style_treeview(self):
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        fg_color = "#DCE4EE" if is_dark else "#333333"
        bg_color = "#2B2B2B" if is_dark else "#FFFFFF"
        header_bg = "#212121" if is_dark else "#F0F0F0"
        selected_bg = "#2C5F8C" if is_dark else "#3399FF"
        header_active_bg = "#313131" if is_dark else "#E0E0E0"

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=bg_color,
                        foreground=fg_color,
                        fieldbackground=bg_color,
                        borderwidth=0,
                        rowheight=30,
                        font=("", 11))
        style.map("Treeview", background=[("selected", selected_bg)])
        style.configure("Treeview.Heading",
                        background=header_bg,
                        foreground=fg_color,
                        relief="flat",
                        font=("", 12, "bold"),
                        padding=(6, 6, 6, 6))
        style.map("Treeview.Heading", background=[("active", header_active_bg)])

    def _init_hint(self):
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        self.txt_steps.insert("end", "여기에 변환 과정이 표시됩니다.")
        self.txt_steps.configure(state="disabled")

    def _hist_refresh(self):
        mode = self.var_sort.get()
        query = self.var_search.get().strip()
        sort_map = {
            "최신순": "time_desc",
            "오래된순": "time_asc",
            "입력 A→Z": "expr_asc",
            "입력 Z→A": "expr_desc"
        }
        sort_mode = sort_map.get(mode, "time_desc")
        self._hist_view = self.hist.list_items(query=query, sort_mode=sort_mode)

        for i in self.tree.get_children():
            self.tree.delete(i)

        for idx, it in enumerate(self._hist_view):
            bases = f"{it.base_from}→{it.base_to}"
            self.tree.insert("", "end", iid=str(idx), values=(it.expr, bases, it.result))

    def on_clear(self):
        self.var_input.set("")
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        self.txt_steps.configure(state="disabled")

    def on_hist_load(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        it = self._hist_view[idx]
        self.var_input.set(it.expr)
        self.var_from.set(str(it.base_from))
        self.var_to.set(str(it.base_to))
        self.on_convert()

    def on_convert(self):
        expr = self.var_input.get().strip()
        if not expr:
            messagebox.showerror("오류", "입력 값이 없습니다.")
            return
        try:
            bfrom = int(self.var_from.get())
            if not (2 <= bfrom <= 36):
                raise ValueError(f"입력 진법은 2~36이어야 합니다 (현재: {bfrom})")
            bto = int(self.var_to.get())
            if not (2 <= bto <= 36):
                raise ValueError(f"출력 진법은 2~36이어야 합니다 (현재: {bto})")
            prec = int(self.var_prec.get())
            if prec < 0:
                raise ValueError("정밀도는 0 이상이어야 합니다")
            rmode = self.var_round.get()
            if rmode not in ROUND_CHOICES:
                raise ValueError("올바르지 않은 반올림 모드입니다")
        except ValueError as e:
            messagebox.showerror("설정 오류", str(e))
            return

        self.cfg["precision"] = prec
        self.cfg["round_mode"] = rmode
        save_config(self.cfg)

        try:
            out, steps = convert(
                expr=expr,
                base_from=bfrom,
                base_to=bto,
                precision=prec,
                round_mode_str=rmode
            )
        except Exception as e:
            messagebox.showerror("변환 오류", str(e))
            return

        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        for s in steps:
            self.txt_steps.insert("end", s + "\n")
        self.txt_steps.configure(state="disabled")

        self.hist.add(expr, bfrom, bto, out)
        self._hist_refresh()