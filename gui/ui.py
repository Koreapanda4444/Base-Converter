import re
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox, END, Scrollbar

from gui import ui_text as T
from history.store import HistoryStore
from converter.logic import convert, to_decimal, from_decimal, evaluate_expression

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

        self._build_panes()
        self._style_treeview()
        self._init_hint()

        self.after(100, self._hist_refresh)

        self.ent_input.bind("<Return>", lambda e: self.on_convert())

    def _init_window_size(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        gw, gh = int(sw*0.6), int(sh*0.65)
        gw = max(MIN_W, min(gw, MAX_W))
        gh = max(MIN_H, min(gh, MAX_H))
        x, y = (sw-gw)//2, (sh-gh)//2
        self.geometry(f"{gw}x{gh}+{x}+{y}")
        self.minsize(MIN_W, MIN_H)

    def _build_panes(self):
        pw = tk.PanedWindow(self, orient="horizontal", sashwidth=8, opaqueresize=True)
        pw.pack(side="top", fill="both", expand=True, padx=12, pady=12)

        self.left = ctk.CTkFrame(pw); self.mid = ctk.CTkFrame(pw); self.right = ctk.CTkFrame(pw)
        pw.add(self.left, minsize=380); pw.add(self.mid, minsize=320); pw.add(self.right, minsize=300)

        # LEFT
        self.left.grid_columnconfigure(0, weight=1)

        inp = ctk.CTkFrame(self.left); inp.grid(row=0, column=0, sticky="ew", pady=(0,10))
        inp.grid_columnconfigure(8, weight=1)

        ctk.CTkLabel(inp, text=T.LBL_INPUT).grid(row=0, column=0, sticky="w")
        self.var_input = tk.StringVar(value="")
        self.ent_input = ctk.CTkEntry(inp, textvariable=self.var_input, placeholder_text="예: 1011.01  또는  A.F + 10")
        self.ent_input.grid(row=1, column=0, columnspan=9, sticky="ew", pady=(2,8))

        ctk.CTkLabel(inp, text=T.LBL_FROM).grid(row=2, column=0, sticky="w")
        self.var_from = tk.StringVar(value="10")
        self.cmb_from = ctk.CTkComboBox(inp, values=T.BASES, variable=self.var_from, width=90)
        self.cmb_from.grid(row=3, column=0, sticky="w")

        ctk.CTkLabel(inp, text=T.LBL_TO).grid(row=2, column=1, sticky="w")
        self.var_to = tk.StringVar(value="2")
        self.cmb_to = ctk.CTkComboBox(inp, values=T.BASES, variable=self.var_to, width=90)
        self.cmb_to.grid(row=3, column=1, sticky="w", padx=(6,0))

        self.btn_convert = ctk.CTkButton(inp, text=T.BTN_CONVERT, command=self.on_convert, width=110)
        self.btn_convert.grid(row=3, column=2, padx=(12,6))
        self.btn_swap = ctk.CTkButton(inp, text=T.BTN_SWAP, command=self.on_swap, width=70)
        self.btn_swap.grid(row=3, column=3, padx=6)
        self.btn_clear = ctk.CTkButton(inp, text=T.BTN_CLEAR, command=self.on_clear, width=80)
        self.btn_clear.grid(row=3, column=4, padx=6)

        ctk.CTkLabel(self.left, text=T.LBL_RESULT).grid(row=4, column=0, sticky="w")
        res_row = ctk.CTkFrame(self.left); res_row.grid(row=5, column=0, sticky="ew", pady=(2,6))
        res_row.grid_columnconfigure(0, weight=1)
        self.var_result = tk.StringVar(value="")
        self.ent_result = ctk.CTkEntry(res_row, textvariable=self.var_result, state="readonly")
        self.ent_result.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(res_row, text=T.BTN_COPY, width=60, command=lambda: self._copy_to_clip(self.ent_result.get())).grid(row=0, column=1, padx=(6,0))

        ctk.CTkLabel(self.left, text=T.LBL_SUMMARY).grid(row=6, column=0, sticky="w", pady=(6,2))
        self.sum2 = self._mk_sum_row(self.left, 7, "2진")
        self.sum8 = self._mk_sum_row(self.left, 8, "8진")
        self.sum10= self._mk_sum_row(self.left, 9, "10진")
        self.sum16= self._mk_sum_row(self.left,10, "16진")

        # MID
        self.mid.grid_columnconfigure(0, weight=1)
        self.mid.grid_rowconfigure(1, weight=1)
        self.lbl_steps = ctk.CTkLabel(self.mid, text=T.LBL_STEPS)
        self.lbl_steps.grid(row=0, column=0, sticky="w")
        self.txt_steps = ctk.CTkTextbox(self.mid, wrap="word")
        self.txt_steps.grid(row=1, column=0, sticky="nsew")

        # RIGHT (history)
        self.right.grid_columnconfigure(0, weight=1)
        self.right.grid_rowconfigure(1, weight=1)
        head = ctk.CTkFrame(self.right, fg_color="transparent"); head.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(head, text=T.LBL_HISTORY).pack(side="left")
        wrap = ctk.CTkFrame(self.right); wrap.grid(row=1, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1); wrap.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(wrap, columns=("expr","bases","result"), show="headings", selectmode="browse")
        self.tree.heading("expr", text="입력"); self.tree.heading("bases", text="진법"); self.tree.heading("result", text="결과")
        self.tree.column("expr", width=220, anchor="w"); self.tree.column("bases", width=80, anchor="center"); self.tree.column("result", width=170, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = Scrollbar(wrap, orient="vertical", command=self.tree.yview); sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", self.on_hist_load); self.tree.bind("<Return>", self.on_hist_load)

        self.status = ctk.CTkLabel(self, text=""); self.status.pack(side="bottom", fill="x", padx=12, pady=(0,6))

    def _mk_sum_row(self, parent, r, label):
        fr = ctk.CTkFrame(parent); fr.grid(row=r, column=0, sticky="ew", pady=2)
        fr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fr, text=label, width=40).grid(row=0, column=0, sticky="w")
        entry = ctk.CTkEntry(fr, state="readonly"); entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(fr, text=T.BTN_COPY, width=60, command=lambda e=entry: self._copy_to_clip(e.get())).grid(row=0, column=2, padx=(6,0))
        return entry

    def _style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=24)

    def _init_hint(self):
        self.txt_steps.configure(state="normal"); self.txt_steps.delete("1.0","end"); self.txt_steps.insert("end", T.HINT); self.txt_steps.configure(state="disabled")

    def _hist_refresh(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for idx, item in enumerate(self.hist.items):
            bases = f"{item.base_from}→{item.base_to}"
            self.tree.insert("", "end", iid=str(idx), values=(item.expr, bases, item.result))

    # events
    def _copy_to_clip(self, text: str):
        if not text: return
        try:
            self.clipboard_clear(); self.clipboard_append(text)
            self.status.configure(text="클립보드에 복사됨")
        except Exception:
            pass

    def on_swap(self):
        f, t = self.var_from.get(), self.var_to.get()
        self.var_from.set(t); self.var_to.set(f)

    def on_clear(self):
        self.var_input.set(""); self.var_result.set("")
        for e in (self.sum2, self.sum8, self.sum10, self.sum16):
            e.configure(state="normal"); e.delete(0, END); e.configure(state="readonly")
        self._init_hint(); self.status.configure(text="")

    def on_hist_load(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0]); item = self.hist.get(idx)
        if not item: return
        self.var_input.set(item.expr)
        self.var_from.set(str(item.base_from))
        self.var_to.set(str(item.base_to))
        self._recompute(add_history=False)
        self.status.configure(text="히스토리에서 불러옴")

    def on_convert(self):
        self._recompute(add_history=True)

    def _recompute(self, add_history: bool):
        expr = self.var_input.get().strip()
        if not expr:
            messagebox.showerror("오류", "입력 값이 비어 있습니다."); return
        try:
            base_from = int(self.var_from.get()); base_to = int(self.var_to.get())
        except Exception:
            messagebox.showerror("오류", "진법 선택이 잘못되었습니다."); return
        try:
            out, steps = convert(expr, base_from, base_to)
        except Exception as e:
            messagebox.showerror("변환 실패", f"{T.ERR_INVALID}\n\n{e}"); return

        self.var_result.set(out)

        self.txt_steps.configure(state="normal"); self.txt_steps.delete("1.0","end")
        for s in steps: self.txt_steps.insert("end", s+"\n")
        self.txt_steps.configure(state="disabled")

        try:
            if any(c in expr for c in "+-*/()"):
                dec, _ = evaluate_expression(expr, base_from)
            else:
                dec, _ = to_decimal(expr, base_from)
            b2, _ = from_decimal(dec, 2); b8, _ = from_decimal(dec, 8); b10 = str(dec); b16, _ = from_decimal(dec,16)
            for entry, val in ((self.sum2,b2),(self.sum8,b8),(self.sum10,b10),(self.sum16,b16)):
                entry.configure(state="normal"); entry.delete(0, END); entry.insert(0, val); entry.configure(state="readonly")
        except Exception:
            pass

        if add_history:
            self.hist.add(expr, base_from, base_to, out)
            self._hist_refresh()

def run():
    app = App()
    app.mainloop()
