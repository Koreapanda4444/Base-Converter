import tkinter as tk
import customtkinter as ctk
from tkinter import colorchooser, messagebox, END, Scrollbar, ttk, filedialog
from gui import ui_text_kr as KR
from gui import ui_text_en as EN
from gui.config_manager import load_config, save_config
from gui.theme_manager import load_theme, save_theme, apply_theme
from history.store import HistoryStore
from converter.logic import convert

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.lang = self.config_data.get("language", "KR")
        self.texts = KR if self.lang == "KR" else EN
        self.theme = load_theme()
        apply_theme(self.theme)
        ctk.set_appearance_mode("system")
        self.title(self.texts.APP_TITLE)
        self.geometry("1000x700")
        self.minsize(900, 560)
        self.hist = HistoryStore()
        self._hist_view = []
        self._build_ui()
        self._hist_refresh()

    def _build_ui(self):
        topbar = ctk.CTkFrame(self)
        topbar.pack(fill="x", padx=10, pady=6)
        self.lang_btn = ctk.CTkSegmentedButton(topbar, values=["KR", "EN"], command=self._on_lang_change)
        self.lang_btn.set(self.lang)
        self.lang_btn.pack(side="right", padx=(0, 10))
        ctk.CTkLabel(topbar, text="정밀도").pack(side="left")
        self.prec_var = tk.IntVar(value=self.config_data.get("precision", 12))
        ctk.CTkEntry(topbar, textvariable=self.prec_var, width=50).pack(side="left", padx=6)
        ctk.CTkLabel(topbar, text="반올림").pack(side="left")
        self.round_var = tk.StringVar(value=self.config_data.get("round_mode", "HALF_UP"))
        ctk.CTkComboBox(topbar, values=["HALF_UP", "HALF_DOWN", "HALF_EVEN", "CEILING", "FLOOR"], variable=self.round_var, width=120).pack(side="left", padx=6)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)
        ctk.CTkLabel(main_frame, text=self.texts.LBL_INPUT).grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar(value="")
        ctk.CTkEntry(main_frame, textvariable=self.input_var).grid(row=0, column=1, sticky="ew", pady=4)
        ctk.CTkLabel(main_frame, text=self.texts.LBL_FROM).grid(row=1, column=0, sticky="w")
        self.base_from = tk.StringVar(value="10")
        ctk.CTkComboBox(main_frame, values=[str(i) for i in range(2, 37)], variable=self.base_from, width=80).grid(row=1, column=1, sticky="w")
        ctk.CTkLabel(main_frame, text=self.texts.LBL_TO).grid(row=1, column=1, sticky="e", padx=(0, 120))
        self.base_to = tk.StringVar(value="2")
        ctk.CTkComboBox(main_frame, values=[str(i) for i in range(2, 37)], variable=self.base_to, width=80).place(relx=0.9, rely=0.22)
        ctk.CTkLabel(main_frame, text=self.texts.LBL_RESULT).grid(row=2, column=0, sticky="nw")
        self.result_var = tk.StringVar(value="")
        ctk.CTkEntry(main_frame, textvariable=self.result_var, state="readonly").grid(row=2, column=1, sticky="ew", pady=(0, 6))
        ctk.CTkButton(main_frame, text=self.texts.BTN_CONVERT, command=self.on_convert).grid(row=3, column=1, sticky="e", pady=(6, 0))

        self.tree = ttk.Treeview(main_frame, columns=("expr", "result"), show="headings", selectmode="browse")
        self.tree.heading("expr", text="입력")
        self.tree.heading("result", text="결과")
        self.tree.column("expr", width=380, anchor="w")
        self.tree.column("result", width=260, anchor="w")
        self.tree.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        self.tree.bind("<Double-1>", self.on_hist_load)
        sb = Scrollbar(main_frame, command=self.tree.yview)
        sb.grid(row=4, column=2, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        hist_controls = ctk.CTkFrame(self)
        hist_controls.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkButton(hist_controls, text="📤 CSV 내보내기", width=140, command=self.on_hist_export).pack(side="right", padx=(6, 0))
        ctk.CTkButton(hist_controls, text="📥 CSV 가져오기", width=140, command=self.on_hist_import).pack(side="right", padx=(0, 6))

        theme_frame = ctk.CTkFrame(self)
        theme_frame.pack(fill="x", padx=10, pady=(4, 10))
        ctk.CTkLabel(theme_frame, text="🎨 Theme Settings").pack(anchor="w", padx=8, pady=(4, 6))
        self.btn_fg = ctk.CTkButton(theme_frame, text="글자색", command=lambda: self._pick_color("text_color"))
        self.btn_bg = ctk.CTkButton(theme_frame, text="배경색", command=lambda: self._pick_color("fg_color"))
        self.btn_main = ctk.CTkButton(theme_frame, text="버튼색", command=lambda: self._pick_color("button_color"))
        self.btn_hover = ctk.CTkButton(theme_frame, text="호버색", command=lambda: self._pick_color("button_hover_color"))
        for btn in (self.btn_fg, self.btn_bg, self.btn_main, self.btn_hover):
            btn.pack(side="left", padx=6, pady=4)

    def _pick_color(self, key):
        color = colorchooser.askcolor(title="색상 선택")[1]
        if not color:
            return
        self.theme["CTk"][key] = [color, color]
        apply_theme(self.theme)
        save_theme(self.theme)

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
            result, _ = convert(expr, base_from, base_to, precision=prec, round_mode_str=round_mode)
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
        if 0 <= idx < len(self._hist_view):
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

    def on_hist_export(self):
        path = filedialog.asksaveasfilename(title="CSV로 내보내기", defaultextension=".csv", filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")], initialfile="history.csv")
        if not path:
            return
        try:
            self.hist.export_csv(path, self._hist_view)
            messagebox.showinfo("완료", "히스토리를 CSV로 저장했습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"CSV 저장 실패\n{e}")

    def on_hist_import(self):
        path = filedialog.askopenfilename(title="CSV 가져오기", filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")])
        if not path:
            return
        ans = messagebox.askyesnocancel("가져오기 모드", "예: 기존 히스토리에 추가(append)\n아니오: 기존 히스토리를 대체(replace)\n취소: 중단")
        if ans is None:
            return
        mode = "append" if ans else "replace"
        try:
            self.hist.import_csv(path, mode=mode)
            self._hist_refresh()
            msg = "추가 완료" if mode == "append" else "대체 완료"
            messagebox.showinfo("완료", f"CSV {msg}되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"CSV 가져오기 실패\n{e}")

def run():
    app = App()
    app.mainloop()