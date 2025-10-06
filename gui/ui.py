import tkinter as tk
import customtkinter as ctk
from tkinter import colorchooser, messagebox, END, Scrollbar, ttk, filedialog, simpledialog
from gui import ui_text_kr as KR
from gui import ui_text_en as EN
from gui.config_manager import load_config, save_config
from gui.theme_manager import load_theme, save_theme, apply_theme
from history.store import HistoryStore
from converter.logic import convert

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.lang = self.cfg.get("language", "KR")
        self.texts = KR if self.lang == "KR" else EN
        self.theme = load_theme()
        apply_theme(self.theme)
        ctk.set_appearance_mode("system")
        self.title(self.texts.APP_TITLE)
        self.geometry("1120x760"); self.minsize(980, 620)
        self.hist = HistoryStore(); self._hist_view = []
        self._build_ui(); self._bind_keys()
        self._hist_refresh()

    def _build_ui(self):
        top = ctk.CTkFrame(self); top.pack(fill="x", padx=10, pady=6)
        self.lang_btn = ctk.CTkSegmentedButton(top, values=["KR", "EN"], command=self._on_lang_change)
        self.lang_btn.set(self.lang); self.lang_btn.pack(side="right", padx=(0, 10))
        ctk.CTkLabel(top, text="정밀도").pack(side="left")
        self.prec_var = tk.IntVar(value=self.cfg.get("precision", 12))
        ctk.CTkEntry(top, textvariable=self.prec_var, width=50).pack(side="left", padx=6)
        ctk.CTkLabel(top, text="반올림").pack(side="left")
        self.round_var = tk.StringVar(value=self.cfg.get("round_mode", "HALF_UP"))
        ctk.CTkComboBox(top, values=["HALF_UP","HALF_DOWN","HALF_EVEN","CEILING","FLOOR"], variable=self.round_var, width=120).pack(side="left", padx=6)
        ctk.CTkLabel(top, text="유효자리수").pack(side="left", padx=(12,2))
        self.sig_var = tk.IntVar(value=int(self.cfg.get("sig", 0)))
        ctk.CTkEntry(top, textvariable=self.sig_var, width=60).pack(side="left", padx=(0,6))
        self.sci_var = tk.BooleanVar(value=bool(self.cfg.get("sci", False)))
        ctk.CTkCheckBox(top, text="과학표기", variable=self.sci_var).pack(side="left")

        main = ctk.CTkFrame(self); main.pack(fill="both", expand=True, padx=10, pady=(0,10))
        main.grid_columnconfigure(1, weight=1); main.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(main, text=self.texts.LBL_INPUT).grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar(value="")
        self.ent_input = ctk.CTkEntry(main, textvariable=self.input_var)
        self.ent_input.grid(row=0, column=1, sticky="ew", pady=4)

        bases = ctk.CTkFrame(main); bases.grid(row=1, column=1, sticky="w")
        ctk.CTkLabel(main, text=self.texts.LBL_FROM).grid(row=1, column=0, sticky="w")
        self.base_from = tk.StringVar(value="10")
        ctk.CTkComboBox(bases, values=[str(i) for i in range(2, 37)], variable=self.base_from, width=80).pack(side="left")
        ctk.CTkLabel(bases, text=self.texts.LBL_TO).pack(side="left", padx=(12,2))
        self.base_to = tk.StringVar(value="2")
        ctk.CTkComboBox(bases, values=[str(i) for i in range(2, 37)], variable=self.base_to, width=80).pack(side="left", padx=(0,4))

        resrow = ctk.CTkFrame(main); resrow.grid(row=2, column=1, sticky="ew", pady=(6,2)); resrow.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(main, text=self.texts.LBL_RESULT).grid(row=2, column=0, sticky="nw")
        self.result_var = tk.StringVar(value="")
        ctk.CTkEntry(resrow, textvariable=self.result_var, state="readonly").grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(resrow, text="복사", width=70, command=lambda:self._copy(self.result_var.get())).grid(row=0, column=1, padx=(6,0))

        ctk.CTkButton(main, text=self.texts.BTN_CONVERT, command=self.on_convert).grid(row=3, column=1, sticky="e", pady=(6,0))

        self.tree = ttk.Treeview(main, columns=("expr","bases","result","fav","tags"), show="headings", selectmode="browse")
        for k,t,w,a in [("expr","입력",380,"w"),("bases","진법",90,"center"),("result","결과",280,"w"),("fav","★",40,"center"),("tags","태그",120,"w")]:
            self.tree.heading(k, text=t); self.tree.column(k, width=w, anchor=a)
        self.tree.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(6,0))
        self.tree.bind("<Double-1>", self.on_hist_load)
        sb = Scrollbar(main, command=self.tree.yview); sb.grid(row=4, column=2, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        hctl = ctk.CTkFrame(self); hctl.pack(fill="x", padx=10, pady=(6,8))
        ctk.CTkButton(hctl, text="★ 토글", width=100, command=self.on_toggle_fav).pack(side="left")
        ctk.CTkButton(hctl, text="#태그 추가", width=110, command=self.on_add_tag).pack(side="left", padx=(6,0))
        ctk.CTkButton(hctl, text="CSV 내보내기", width=120, command=self.on_export_csv).pack(side="right", padx=(6,0))
        ctk.CTkButton(hctl, text="CSV 가져오기", width=120, command=self.on_import_csv).pack(side="right", padx=(6,0))
        ctk.CTkButton(hctl, text="JSON 백업", width=110, command=self.on_export_json).pack(side="right", padx=(6,0))
        ctk.CTkButton(hctl, text="JSON 복원", width=110, command=self.on_import_json).pack(side="right")

        theme = ctk.CTkFrame(self); theme.pack(fill="x", padx=10, pady=(4,10))
        ctk.CTkLabel(theme, text="Theme").pack(anchor="w", padx=8, pady=(4,6))
        for label,key in [("글자색","text_color"),("배경색","fg_color"),("버튼색","button_color"),("호버색","button_hover_color")]:
            ctk.CTkButton(theme, text=label, command=lambda k=key:self._pick_color(k)).pack(side="left", padx=6, pady=4)

    def _bind_keys(self):
        self.bind("<Return>", lambda e:self.on_convert())
        self.bind("<Escape>", lambda e:self._clear())
        self.bind("<Control-c>", lambda e:self._copy(self.result_var.get()))
        self.bind("<Control-f>", lambda e:self._focus_hist())

    def _focus_hist(self):
        self.tree.focus_set()

    def _copy(self, text):
        if not text: return
        try: self.clipboard_clear(); self.clipboard_append(text)
        except Exception: pass

    def _clear(self):
        self.input_var.set(""); self.result_var.set("")

    def _on_lang_change(self, v):
        self.lang = v; self.texts = KR if v=="KR" else EN
        self.title(self.texts.APP_TITLE)
        self._save_cfg()

    def _save_cfg(self):
        save_config({
            "language": self.lang,
            "precision": self.prec_var.get(),
            "round_mode": self.round_var.get(),
            "sig": self.sig_var.get(),
            "sci": bool(self.sci_var.get()),
        })

    def _fmt(self):
        return {
            "letter_case": "upper",
            "group_size": 0,
            "group_sep": " ",
            "prefix": False,
            "sci": bool(self.sci_var.get()),
            "sig": int(self.sig_var.get() or 0),
        }

    def on_convert(self):
        expr = self._normalize(self.input_var.get())
        if not expr:
            messagebox.showerror("오류", "입력값이 없습니다."); return
        try:
            bfrom = int(self.base_from.get()); bto = int(self.base_to.get())
            prec = int(self.prec_var.get()); rmode = self.round_var.get()
            out, _ = convert(expr, bfrom, bto, precision=prec, round_mode_str=rmode, fmt=self._fmt())
            self.result_var.set(out)
            self.hist.add(expr, bfrom, bto, out)
            self._hist_refresh(); self._save_cfg()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_hist_load(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        if 0 <= idx < len(self._hist_view):
            item = self._hist_view[idx]
            self.input_var.set(item.expr); self.base_from.set(str(item.base_from)); self.base_to.set(str(item.base_to))
            self.on_convert(); self._copy(self.result_var.get())

    def on_toggle_fav(self):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        if 0 <= idx < len(self._hist_view):
            item = self._hist_view[idx]
            real_index = self.hist.items.index(item)
            self.hist.toggle_favorite(real_index)
            self._hist_refresh()

    def on_add_tag(self):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        tag = simpledialog.askstring("태그", "추가할 태그(공백없이):", parent=self)
        if not tag: return
        if 0 <= idx < len(self._hist_view):
            item = self._hist_view[idx]
            real_index = self.hist.items.index(item)
            self.hist.add_tag(real_index, tag)
            self._hist_refresh()

    def _hist_refresh(self):
        self._hist_view = self.hist.list_items()
        for i in self.tree.get_children(): self.tree.delete(i)
        for idx, it in enumerate(self._hist_view):
            bases = f"{it.base_from}→{it.base_to}"
            fav = "★" if it.favorite else ""
            self.tree.insert("", "end", iid=str(idx), values=(it.expr, bases, it.result, fav, it.tags or ""))

    def _pick_color(self, key):
        color = colorchooser.askcolor(title="색상 선택")[1]
        if not color: return
        self.theme["CTk"][key] = [color, color]
        apply_theme(self.theme); save_theme(self.theme)

    def on_export_csv(self):
        p = filedialog.asksaveasfilename(title="CSV로 내보내기", defaultextension=".csv", filetypes=[("CSV","*.csv")], initialfile="history.csv")
        if not p: return
        try: self.hist.export_csv(p, self._hist_view); messagebox.showinfo("완료", "CSV 저장됨")
        except Exception as e: messagebox.showerror("오류", str(e))

    def on_import_csv(self):
        p = filedialog.askopenfilename(title="CSV 가져오기", filetypes=[("CSV","*.csv")])
        if not p: return
        ans = messagebox.askyesnocancel("모드", "예: 추가(append)\n아니오: 대체(replace)\n취소: 중단")
        if ans is None: return
        mode = "append" if ans else "replace"
        try: self.hist.import_csv(p, mode); self._hist_refresh(); messagebox.showinfo("완료", "CSV 반영됨")
        except Exception as e: messagebox.showerror("오류", str(e))

    def on_export_json(self):
        p = filedialog.asksaveasfilename(title="JSON 백업", defaultextension=".json", filetypes=[("JSON","*.json")], initialfile="history_backup.json")
        if not p: return
        try: self.hist.export_json(p, self._hist_view); messagebox.showinfo("완료", "JSON 저장됨")
        except Exception as e: messagebox.showerror("오류", str(e))

    def on_import_json(self):
        p = filedialog.askopenfilename(title="JSON 복원", filetypes=[("JSON","*.json")])
        if not p: return
        ans = messagebox.askyesnocancel("모드", "예: 추가(append)\n아니오: 대체(replace)\n취소: 중단")
        if ans is None: return
        mode = "append" if ans else "replace"
        try: self.hist.import_json(p, mode); self._hist_refresh(); messagebox.showinfo("완료", "JSON 반영됨")
        except Exception as e: messagebox.showerror("오류", str(e))

    def _normalize(self, s: str) -> str:
        if not s: return s
        t = s.replace(" ", "")
        t = t.replace("—","-").replace("–","-")
        return t

def run():
    app = App(); app.mainloop()
