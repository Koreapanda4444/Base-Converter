import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox, END, filedialog
import json
import os

from gui.ui_text_kr import T
from gui.help_text_kr import HELP_TEXT
from gui.theme_manager import apply_theme, set_theme
from converter.logic import convert, to_decimal, from_decimal, evaluate_expression
from history.store import HistoryStore

MIN_W, MIN_H = 900, 560

ROUND_CHOICES = ["HALF_UP", "HALF_DOWN", "HALF_EVEN", "CEILING", "FLOOR"]

SORT_CHOICES = [
    ("최신순", "time_desc"),
    ("오래된순", "time_asc"),
    ("입력 A→Z", "expr_asc"),
    ("입력 Z→A", "expr_desc"),
    ("결과 A→Z", "result_asc"),
    ("결과 Z→A", "result_desc"),
]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_theme()
        self.title(T.APP_TITLE)
        self._init_window_size()

        self.hist = HistoryStore()
        self._hist_view = []

        self._build_ui()
        self._style_treeview()
        self._init_hint()

        self.after(100, self._hist_refresh)

    def _init_window_size(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        gw, gh = int(sw * 0.6), int(sh * 0.65)
        gw = max(MIN_W, gw)
        gh = max(MIN_H, gh)
        x, y = (sw - gw) // 2, (sh - gh) // 2
        self.geometry(f"{gw}x{gh}+{x}+{y}")
        self.minsize(MIN_W, MIN_H)

    def _build_ui(self):
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=6)

        self.var_input = tk.StringVar()
        ctk.CTkLabel(top, text=T.LBL_INPUT).pack(anchor="w")
        self.ent_input = ctk.CTkEntry(top, textvariable=self.var_input)
        self.ent_input.pack(fill="x", pady=4)

        opt = ctk.CTkFrame(top)
        opt.pack(fill="x", pady=4)

        ctk.CTkLabel(opt, text=T.LBL_FROM).grid(row=0, column=0, sticky="w")
        self.var_from = tk.StringVar(value="10")
        self.cmb_from = ctk.CTkComboBox(opt, values=T.BASES, variable=self.var_from, width=80)
        self.cmb_from.grid(row=1, column=0, padx=2)

        ctk.CTkLabel(opt, text=T.LBL_TO).grid(row=0, column=1)
        self.var_to = tk.StringVar(value="2")
        self.cmb_to = ctk.CTkComboBox(opt, values=T.BASES, variable=self.var_to, width=80)
        self.cmb_to.grid(row=1, column=1, padx=2)

        ctk.CTkLabel(opt, text="정밀도").grid(row=0, column=2)
        self.var_prec = tk.IntVar(value=12)
        ctk.CTkEntry(opt, textvariable=self.var_prec, width=60).grid(row=1, column=2, padx=4)

        ctk.CTkLabel(opt, text="반올림").grid(row=0, column=3)
        self.var_round = tk.StringVar(value="HALF_UP")
        ctk.CTkComboBox(opt, values=ROUND_CHOICES, variable=self.var_round, width=120).grid(row=1, column=3, padx=4)

        ctk.CTkButton(opt, text=T.BTN_CONVERT, command=self.on_convert).grid(row=1, column=4, padx=6)
        ctk.CTkButton(opt, text=T.BTN_CLEAR, command=self.on_clear).grid(row=1, column=5, padx=6)
        ctk.CTkButton(opt, text=T.BTN_HELP, command=self.on_help).grid(row=1, column=6, padx=6)

        mid = ctk.CTkFrame(self)
        mid.pack(fill="both", expand=True, padx=10, pady=6)
        mid.grid_columnconfigure(1, weight=1)
        mid.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(mid, text=T.LBL_STEPS).grid(row=0, column=1, sticky="w")
        self.txt_steps = ctk.CTkTextbox(mid)
        self.txt_steps.grid(row=1, column=1, sticky="nsew", padx=6)

        right = ctk.CTkFrame(self)
        right.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(right)
        head.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(head, text="검색").pack(side="left")
        self.var_search = tk.StringVar()
        ent_search = ctk.CTkEntry(head, textvariable=self.var_search, width=150)
        ent_search.pack(side="left", padx=4)
        ent_search.bind("<KeyRelease>", lambda e: self._hist_refresh())

        ctk.CTkLabel(head, text="정렬").pack(side="left", padx=(10, 4))
        self.var_sort = tk.StringVar(value="최신순")
        cmb_sort = ctk.CTkComboBox(head, values=[x[0] for x in SORT_CHOICES],
                                   variable=self.var_sort, width=120)
        cmb_sort.pack(side="left")
        cmb_sort.bind("<<ComboboxSelected>>", lambda e: self._hist_refresh())

        wrap = ctk.CTkFrame(right)
        wrap.grid(row=1, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            wrap,
            columns=("expr", "bases", "result"),
            show="headings"
        )
        self.tree.heading("expr", text="입력")
        self.tree.heading("bases", text="진법")
        self.tree.heading("result", text="결과")
        self.tree.column("expr", width=190)
        self.tree.column("bases", width=70, anchor="center")
        self.tree.column("result", width=150)
        self.tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self.on_hist_load)

    def _style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=24)

    def _init_hint(self):
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        self.txt_steps.insert("end", T.HINT)
        self.txt_steps.configure(state="disabled")

    def _hist_refresh(self):
        label = self.var_sort.get()
        sort_mode = next((code for text, code in SORT_CHOICES if text == label), "time_desc")
        query = self.var_search.get()
        self._hist_view = self.hist.list_items(query=query, sort_mode=sort_mode)

        for iid in self.tree.get_children():
            self.tree.delete(iid)

        for idx, h in enumerate(self._hist_view):
            bases = f"{h.base_from}→{h.base_to}"
            self.tree.insert("", "end", iid=str(idx),
                             values=(h.expr, bases, h.result))

    def on_help(self):
        win = ctk.CTkToplevel(self)
        win.title("도움말")
        txt = ctk.CTkTextbox(win, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("end", HELP_TEXT)
        txt.configure(state="disabled")

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
        item = self._hist_view[idx]
        self.var_input.set(item.expr)
        self.var_from.set(str(item.base_from))
        self.var_to.set(str(item.base_to))
        self.on_convert()

    def on_convert(self):
        expr = self.var_input.get().strip()
        if not expr:
            messagebox.showerror("오류", T.ERR_EMPTY)
            return

        try:
            bfrom = int(self.var_from.get())
            bto = int(self.var_to.get())
            prec = int(self.var_prec.get())
            rmode = self.var_round.get()
        except:
            messagebox.showerror("오류", T.ERR_SETTING)
            return

        try:
            out, steps = convert(expr, bfrom, bto, precision=prec, round_mode_str=rmode)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return

        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        for s in steps:
            self.txt_steps.insert("end", s + "\n")
        self.txt_steps.configure(state="disabled")

        self.hist.add(expr, bfrom, bto, out)
        self._hist_refresh()
