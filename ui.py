import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, Listbox, END, Scrollbar
import re

import ui_text as T
from history import HistoryStore
from converter import convert, to_decimal, from_decimal, evaluate_expression


MIN_W, MIN_H = 900, 560
MAX_W, MAX_H = 1600, 1000


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title(T.APP_TITLE)
        self._init_window_size()
        self.hist = HistoryStore()
        self._build_top_controls()
        self._build_resizable_panes()
        self._init_hint()
        self.after(100, self._hist_refresh)   # ✅ UI 다 뜬 뒤에 실행

    # ---------------- Window sizing ----------------
    def _init_window_size(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        gw, gh = int(sw * 0.60), int(sh * 0.65)
        gw = max(MIN_W, min(gw, MAX_W))
        gh = max(MIN_H, min(gh, MAX_H))
        x, y = (sw - gw) // 2, (sh - gh) // 2
        self.geometry(f"{gw}x{gh}+{x}+{y}")
        self.minsize(MIN_W, MIN_H)

    # ---------------- TOP: 입력/진법/버튼 ----------------
    def _build_top_controls(self):
        top = ctk.CTkFrame(self)
        top.pack(side="top", fill="x", padx=12, pady=(12, 8))

        ctk.CTkLabel(top, text=T.LBL_INPUT).grid(row=0, column=0, sticky="w")
        self.var_input = ctk.StringVar(value="")
        self.ent_input = ctk.CTkEntry(
            top, textvariable=self.var_input, placeholder_text="예: 1011.01  또는  A.F + 10"
        )
        self.ent_input.grid(row=1, column=0, columnspan=8, sticky="ew", pady=(2, 8))

        ctk.CTkLabel(top, text=T.LBL_FROM).grid(row=2, column=0, sticky="w")
        self.var_from = ctk.StringVar(value="10")
        self.cmb_from = ctk.CTkComboBox(top, values=T.BASES, variable=self.var_from, width=100)
        self.cmb_from.grid(row=3, column=0, sticky="w")

        ctk.CTkLabel(top, text=T.LBL_TO).grid(row=2, column=1, sticky="w")
        self.var_to = ctk.StringVar(value="2")
        self.cmb_to = ctk.CTkComboBox(top, values=T.BASES, variable=self.var_to, width=100)
        self.cmb_to.grid(row=3, column=1, sticky="w", padx=(6, 0))

        self.btn_convert = ctk.CTkButton(top, text=T.BTN_CONVERT, command=self.on_convert, width=110)
        self.btn_convert.grid(row=3, column=2, padx=(12, 6))
        self.btn_swap = ctk.CTkButton(top, text=T.BTN_SWAP, command=self.on_swap, width=70)
        self.btn_swap.grid(row=3, column=3, padx=6)
        self.btn_clear = ctk.CTkButton(top, text=T.BTN_CLEAR, command=self.on_clear, width=80)
        self.btn_clear.grid(row=3, column=4, padx=6)

        top.grid_columnconfigure(7, weight=1)

    # ---------------- CENTER: 3분할 가변 패널 ----------------
    def _build_resizable_panes(self):
        pw = tk.PanedWindow(self, orient="horizontal", sashrelief="flat", sashwidth=8,
                            bg=self.cget("bg"), bd=0, opaqueresize=True)
        pw.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 12))

        left = ctk.CTkFrame(pw)
        mid = ctk.CTkFrame(pw)
        right = ctk.CTkFrame(pw)

        pw.add(left,  minsize=260)
        pw.add(mid,   minsize=280)
        pw.add(right, minsize=240)

        # LEFT: 결과 + 요약
        left.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(left, text=T.LBL_RESULT).grid(row=0, column=0, sticky="w")
        self.var_result = ctk.StringVar(value="")
        res_row = ctk.CTkFrame(left)
        res_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        res_row.grid_columnconfigure(0, weight=1)
        self.ent_result = ctk.CTkEntry(res_row, textvariable=self.var_result)
        self.ent_result.grid(row=0, column=0, sticky="ew")
        self.ent_result.configure(state="readonly")
        ctk.CTkButton(res_row, text="복사", width=60,
                      command=lambda: self._copy_to_clip(self.ent_result.get())
                      ).grid(row=0, column=1, padx=(6, 0))

        ctk.CTkLabel(left, text=T.LBL_SUMMARY).grid(row=2, column=0, sticky="w", pady=(6, 2))
        self.sum2 = ctk.CTkEntry(left);  self._mk_ro(self.sum2)
        self.sum8 = ctk.CTkEntry(left);  self._mk_ro(self.sum8)
        self.sum10 = ctk.CTkEntry(left); self._mk_ro(self.sum10)
        self.sum16 = ctk.CTkEntry(left); self._mk_ro(self.sum16)
        self._row(left, 3, "2진", self.sum2)
        self._row(left, 4, "8진", self.sum8)
        self._row(left, 5, "10진", self.sum10)
        self._row(left, 6, "16진", self.sum16)

        # MIDDLE: 변환/계산 과정
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_rowconfigure(1, weight=1)
        self.lbl_steps = ctk.CTkLabel(mid, text=T.LBL_STEPS)
        self.lbl_steps.grid(row=0, column=0, sticky="w")
        self.txt_steps = ctk.CTkTextbox(mid, wrap="word")
        self.txt_steps.grid(row=1, column=0, sticky="nsew")

        # RIGHT: 히스토리
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        head = ctk.CTkFrame(right, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(head, text=T.LBL_HISTORY).pack(side="left")
        ctk.CTkLabel(head, text="더블클릭/Enter로 불러오기", text_color=("gray70", "gray60")).pack(side="right")

        hist_wrap = ctk.CTkFrame(right)
        hist_wrap.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        hist_wrap.grid_columnconfigure(0, weight=1)
        hist_wrap.grid_rowconfigure(0, weight=1)

        # ✅ 테마에 맞춘 Listbox
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            lb_bg, lb_fg, lb_selbg, lb_selfg = "#1f1f1f", "#eaeaea", "#3a7ebf", "#ffffff"
        else:
            lb_bg, lb_fg, lb_selbg, lb_selfg = "#ffffff", "#222222", "#cde4ff", "#000000"

        self.lst_hist = Listbox(
            hist_wrap,
            exportselection=False,
            bg=lb_bg, fg=lb_fg,
            selectbackground=lb_selbg, selectforeground=lb_selfg,
            highlightthickness=0, borderwidth=0
        )
        self.lst_hist.grid(row=0, column=0, sticky="nsew")
        sb = Scrollbar(hist_wrap, orient="vertical", command=self.lst_hist.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.lst_hist.configure(yscrollcommand=sb.set)
        self.lst_hist.bind("<Double-Button-1>", self.on_hist_load)
        self.lst_hist.bind("<Return>", self.on_hist_load)

        self.after(50, lambda: self._init_sash_positions(pw))

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(side="bottom", fill="x", padx=12, pady=(0, 6))

    def _init_sash_positions(self, pw: tk.PanedWindow):
        total = pw.winfo_width()
        if total > 1:
            x1, x2 = int(total * 0.33), int(total * 0.67)
            pw.sash_place(0, x1, 1)
            pw.sash_place(1, x2, 1)

    def _init_hint(self):
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        self.txt_steps.insert("end", T.HINT)
        self.txt_steps.configure(state="disabled")

    # ---------------- Utilities ----------------
    def _mk_ro(self, entry: ctk.CTkEntry):
        entry.configure(state="readonly")

    def _row(self, parent, r, label, entry):
        fr = ctk.CTkFrame(parent)
        fr.grid(row=r, column=0, sticky="ew", pady=2)
        fr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fr, text=label, width=40).grid(row=0, column=0, sticky="w")
        entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(fr, text="복사", width=60,
                      command=lambda e=entry: self._copy_to_clip(e.get())
                      ).grid(row=0, column=2, padx=(6, 0))

    def _copy_to_clip(self, text: str):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass

    def _hist_refresh(self):
        self.lst_hist.delete(0, END)
        for line in self.hist.list_texts():
            self.lst_hist.insert(END, line)

    # ---------------- Events ----------------
    def on_swap(self):
        f, t = self.var_from.get(), self.var_to.get()
        self.var_from.set(t)
        self.var_to.set(f)

    def on_clear(self):
        self.var_input.set("")
        self.var_result.set("")
        for e in (self.sum2, self.sum8, self.sum10, self.sum16):
            e.configure(state="normal"); e.delete(0, END); e.configure(state="readonly")
        self._init_hint()
        self.status.configure(text="")

    def on_hist_load(self, event=None):
        idxs = self.lst_hist.curselection()
        if not idxs:
            return
        item = self.hist.get(idxs[0])
        if not item:
            return
        self.var_input.set(item.expr)
        self.var_from.set(str(item.base_from))
        self.var_to.set(str(item.base_to))
        self.var_result.set(item.result)
        self.status.configure(text="히스토리에서 불러옴")

    def on_convert(self):
        expr = self.var_input.get().strip()
        try:
            base_from = int(self.var_from.get())
            base_to = int(self.var_to.get())
        except Exception:
            messagebox.showerror("오류", "진법 선택이 잘못되었습니다.")
            return

        if not expr:
            messagebox.showerror("오류", "입력 값이 비어 있습니다.")
            return

        is_expr = bool(re.search(r"[+\-*/()]", expr))
        self.lbl_steps.configure(text=("계산 과정" if is_expr else "변환 과정"))

        try:
            out, steps = convert(expr, base_from, base_to)
        except Exception as e:
            messagebox.showerror("변환 실패", f"{T.ERR_INVALID}\n\n{e}")
            return

        self.var_result.set(out)
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        for s in steps:
            self.txt_steps.insert("end", s + "\n")
        self.txt_steps.configure(state="disabled")

        try:
            if is_expr:
                dec, _ = evaluate_expression(expr, base_from)
            else:
                dec, _ = to_decimal(expr, base_from)
            b2, _ = from_decimal(dec, 2)
            b8, _ = from_decimal(dec, 8)
            b10 = f"{dec}"
            b16, _ = from_decimal(dec, 16)
            for entry, val in ((self.sum2, b2), (self.sum8, b8), (self.sum10, b10), (self.sum16, b16)):
                entry.configure(state="normal"); entry.delete(0, END); entry.insert(0, val); entry.configure(state="readonly")
        except Exception:
            pass

        self.hist.add(expr, base_from, base_to, out)
        self._hist_refresh()
        self.status.configure(text="완료")
