import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, END, Scrollbar
from tkinter import ttk
import re

import ui_text as T
from history import HistoryStore
from converter import convert, to_decimal, from_decimal, evaluate_expression

MIN_W, MIN_H = 900, 560
MAX_W, MAX_H = 1600, 1000

_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def _digval(ch: str) -> int:
    ch = ch.upper()
    if ch in _DIGITS:
        return _DIGITS.index(ch)
    return -1

def _max_digit_char(base: int) -> str:
    return _DIGITS[base-1] if 2 <= base <= 36 else "?"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title(T.APP_TITLE)
        self._init_window_size()
        self.hist = HistoryStore()

        # 레이아웃
        self._build_resizable_panes()
        self._style_treeview()
        self._init_hint()

        # 초기 렌더
        self.after(100, self._hist_refresh)

        # 단축키
        self.ent_input.bind("<Return>", lambda e: self.on_convert())
        self.bind("<Delete>", lambda e: self.del_selected())
        self.bind("<Control-c>", lambda e: self._copy_and_flash(self.var_result.get()))
        self.bind("<Control-C>", lambda e: self._copy_and_flash(self.var_result.get()))
        self.bind("<Control-l>", lambda e: self._shortcut_clear())
        self.bind("<Control-L>", lambda e: self._shortcut_clear())
        self.bind("<Control-Up>",   lambda e: self._step_base(self.var_to, +1))
        self.bind("<Control-Down>", lambda e: self._step_base(self.var_to, -1))
        self.bind("<Control-Shift-Up>",   lambda e: self._step_base(self.var_from, +1))
        self.bind("<Control-Shift-Down>", lambda e: self._step_base(self.var_from, -1))
        self.bind("<Control-h>", lambda e: self._focus_history())
        self.bind("<Control-H>", lambda e: self._focus_history())

        # 실시간 프리체크
        self.ent_input.bind("<KeyRelease>", self._on_input_changed)

    # ---------------- Window sizing ----------------
    def _init_window_size(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        gw, gh = int(sw * 0.60), int(sh * 0.65)
        gw = max(MIN_W, min(gw, MAX_W))
        gh = max(MIN_H, min(gh, MAX_H))
        x, y = (sw - gw) // 2, (sh - gh) // 2
        self.geometry(f"{gw}x{gh}+{x}+{y}")
        self.minsize(MIN_W, MIN_H)

    # ---------------- CENTER: 3분할 ----------------
    def _build_resizable_panes(self):
        pw = tk.PanedWindow(self, orient="horizontal", sashrelief="flat", sashwidth=8,
                            bg=self.cget("bg"), bd=0, opaqueresize=True)
        pw.pack(side="top", fill="both", expand=True, padx=12, pady=12)

        self.left = ctk.CTkFrame(pw)
        self.mid = ctk.CTkFrame(pw)
        self.right = ctk.CTkFrame(pw)

        pw.add(self.left,  minsize=400)
        pw.add(self.mid,   minsize=320)
        pw.add(self.right, minsize=300)

        self._build_left_panel(self.left)

        # 가운데: 과정 + 연산 트레이스
        self.mid.grid_columnconfigure(0, weight=1)
        self.mid.grid_rowconfigure(3, weight=1)

        self.lbl_steps = ctk.CTkLabel(self.mid, text=T.LBL_STEPS)
        self.lbl_steps.grid(row=0, column=0, sticky="w")

        self.trace_controls = ctk.CTkFrame(self.mid)
        self.trace_controls.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.trace_controls.grid_columnconfigure(3, weight=1)

        self.var_show_trace = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.trace_controls, text="연산 트레이스 보기", variable=self.var_show_trace).grid(row=0, column=0, padx=(0,8))
        ctk.CTkLabel(self.trace_controls, text="(표시 전용, 수치 계산은 converter 사용)").grid(row=0, column=1, sticky="w")

        self.txt_steps = ctk.CTkTextbox(self.mid, wrap="word")
        self.txt_steps.grid(row=3, column=0, sticky="nsew")

        # 오른쪽: 히스토리
        self._build_history_panel(self.right)

        self.after(50, lambda: self._init_sash_positions(pw))

        # 상태바
        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(side="bottom", fill="x", padx=12, pady=(0, 6))

    def _build_left_panel(self, parent: ctk.CTkFrame):
        parent.grid_columnconfigure(0, weight=1)

        # --- 입력 블록 ---
        inp = ctk.CTkFrame(parent)
        inp.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        inp.grid_columnconfigure(12, weight=1)

        ctk.CTkLabel(inp, text=T.LBL_INPUT).grid(row=0, column=0, sticky="w")
        self.var_input = ctk.StringVar(value="")
        self.ent_input = ctk.CTkEntry(inp, textvariable=self.var_input,
                                      placeholder_text="예: (A.F + 10) * 2  또는  1011.01")
        self.ent_input.grid(row=1, column=0, columnspan=13, sticky="ew", pady=(2, 8))

        ctk.CTkLabel(inp, text=T.LBL_FROM).grid(row=2, column=0, sticky="w")
        self.var_from = ctk.StringVar(value="10")
        self.cmb_from = ctk.CTkComboBox(inp, values=T.BASES, variable=self.var_from, width=92)
        self.cmb_from.grid(row=3, column=0, sticky="w")

        ctk.CTkLabel(inp, text=T.LBL_TO).grid(row=2, column=1, sticky="w")
        self.var_to = ctk.StringVar(value="2")
        self.cmb_to = ctk.CTkComboBox(inp, values=T.BASES, variable=self.var_to, width=92)
        self.cmb_to.grid(row=3, column=1, sticky="w", padx=(6, 0))

        # 정밀도/반올림
        ctk.CTkLabel(inp, text="소수 자릿수").grid(row=2, column=2, sticky="w", padx=(12, 0))
        self.var_prec = ctk.StringVar(value="8")
        self.cmb_prec = ctk.CTkComboBox(inp, values=["0","2","4","8","12","16","24","32"],
                                        variable=self.var_prec, width=70)
        self.cmb_prec.grid(row=3, column=2, sticky="w")

        ctk.CTkLabel(inp, text="반올림").grid(row=2, column=3, sticky="w", padx=(12, 0))
        self.var_rmode = ctk.StringVar(value="round")
        self.cmb_rmode = ctk.CTkComboBox(inp, values=["round","floor","ceil"],
                                         variable=self.var_rmode, width=90)
        self.cmb_rmode.grid(row=3, column=3, sticky="w")

        # 큰 수 줄바꿈 / 다항식
        ctk.CTkLabel(inp, text="줄바꿈").grid(row=2, column=4, sticky="w", padx=(12, 0))
        self.var_wrap = ctk.StringVar(value="없음")
        self.cmb_wrap = ctk.CTkComboBox(inp, values=["없음","32","64","128"],
                                        variable=self.var_wrap, width=80)
        self.cmb_wrap.grid(row=3, column=4, sticky="w")

        self.var_poly = tk.BooleanVar(value=False)
        self.chk_poly = ctk.CTkCheckBox(inp, text="2진 → 다항식(GF(2))", variable=self.var_poly)
        self.chk_poly.grid(row=3, column=5, sticky="w", padx=(12,0))

        self.btn_convert = ctk.CTkButton(inp, text=T.BTN_CONVERT, command=self.on_convert, width=110)
        self.btn_convert.grid(row=3, column=7, padx=(16, 6))
        self.btn_swap = ctk.CTkButton(inp, text=T.BTN_SWAP, command=self.on_swap, width=70)
        self.btn_swap.grid(row=3, column=8, padx=6)
        self.btn_clear = ctk.CTkButton(inp, text=T.BTN_CLEAR, command=self.on_clear, width=80)
        self.btn_clear.grid(row=3, column=9, padx=6)

        # --- 결과 블록 ---
        ctk.CTkLabel(parent, text=T.LBL_RESULT).grid(row=1, column=0, sticky="w")
        res_row = ctk.CTkFrame(parent)
        res_row.grid(row=2, column=0, sticky="ew", pady=(2, 6))
        res_row.grid_columnconfigure(0, weight=1)
        self.var_result = tk.StringVar(value="")
        self.ent_result = ctk.CTkEntry(res_row, textvariable=self.var_result, state="readonly")
        self.ent_result.grid(row=0, column=0, sticky="ew")
        self.ent_result.bind("<Button-1>", lambda e: self._copy_and_flash(self.ent_result.get()))
        ctk.CTkButton(res_row, text=T.BTN_COPY, width=60,
                      command=lambda: self._copy_and_flash(self.ent_result.get())
                      ).grid(row=0, column=1, padx=(6, 0))

        # --- 요약 블록 ---
        ctk.CTkLabel(parent, text=T.LBL_SUMMARY).grid(row=3, column=0, sticky="w", pady=(6, 2))
        self.sum2  = self._mk_summary_row(parent, 4, "2진")
        self.sum8  = self._mk_summary_row(parent, 5, "8진")
        self.sum10 = self._mk_summary_row(parent, 6, "10진")
        self.sum16 = self._mk_summary_row(parent, 7, "16진")

        # 다항식 출력 영역
        self.poly_frame = ctk.CTkFrame(parent)
        self.poly_frame.grid(row=8, column=0, sticky="nsew", pady=(6,0))
        self.poly_frame.grid_columnconfigure(0, weight=1)
        self.lbl_poly = ctk.CTkLabel(self.poly_frame, text="다항식(GF(2))")
        self.lbl_poly.grid(row=0, column=0, sticky="w")
        self.txt_poly = ctk.CTkTextbox(self.poly_frame, height=72, wrap="word")
        self.txt_poly.grid(row=1, column=0, sticky="nsew")
        self.poly_frame.grid_remove()

    def _mk_summary_row(self, parent, r, label_text):
        fr = ctk.CTkFrame(parent)
        fr.grid(row=r, column=0, sticky="ew", pady=2)
        fr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fr, text=label_text, width=40).grid(row=0, column=0, sticky="w")
        entry = ctk.CTkEntry(fr, takefocus=False, state="readonly")
        entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(fr, text=T.BTN_COPY, width=60,
                      command=lambda e=entry: self._copy_and_flash(e.get())
                      ).grid(row=0, column=2, padx=(6, 0))
        entry.bind("<Button-1>", lambda ev, w=entry: self._copy_and_flash(w.get()))
        return entry

    def _build_history_panel(self, parent: ctk.CTkFrame):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        head = ctk.CTkFrame(parent, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(head, text=T.LBL_HISTORY).pack(side="left")

        btns = ctk.CTkFrame(parent, fg_color="transparent")
        btns.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        ctk.CTkButton(btns, text="삭제", width=70, command=self.del_selected).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="전체 삭제", width=90, command=self.clear_hist).pack(side="left", padx=2)

        wrap = ctk.CTkFrame(parent)
        wrap.grid(row=2, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        # 🆕 타입 컬럼 추가
        self.tree = ttk.Treeview(
            wrap,
            columns=("type","expr","bases","result"),
            show="headings",
            selectmode="browse"
        )
        self.tree.heading("type",  text="종류")
        self.tree.heading("expr",  text="입력")
        self.tree.heading("bases", text="진법")
        self.tree.heading("result",text="결과")

        self.tree.column("type",  width=56,  anchor="center")
        self.tree.column("expr",  width=220, anchor="w")
        self.tree.column("bases", width=80,  anchor="center")
        self.tree.column("result",width=170, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        sb = Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.bind("<Double-1>", self.on_hist_load)
        self.tree.bind("<Return>", self.on_hist_load)

    # ---------------- Utilities ----------------
    def _copy_to_clip(self, text: str):
        if not text: return
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status.configure(text="클립보드에 복사됨")
        except Exception:
            pass

    def _flash_border(self, widget, color="#D24747", width=3, ms=220):
        try:
            orig_c = widget.cget("border_color")
            orig_w = widget.cget("border_width") or 1
            widget.configure(border_color=color, border_width=width)
            self.after(ms, lambda: widget.configure(border_color=orig_c, border_width=orig_w))
        except Exception:
            pass

    def _copy_and_flash(self, text: str):
        self._copy_to_clip(text)
        self._flash_border(self.ent_result, color=("#3a7ebf" if ctk.get_appearance_mode()=="Dark" else "#1190ff"))

    def _hist_refresh(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for idx, item in enumerate(self.hist.items):
            kind = "연산" if re.search(r"[+\-*/()]", item.expr) else "변환"
            bases = f"{item.base_from}→{item.base_to}"
            self.tree.insert("", "end", iid=str(idx),
                             values=(kind, item.expr, bases, item.result))

    # ---- 단축키 헬퍼 ----
    def _focus_history(self):
        try:
            self.tree.focus_set()
            cur = self.tree.selection()
            if not cur:
                first = self.tree.get_children()
                if first:
                    self.tree.selection_set(first[0])
            self.status.configure(text="히스토리로 이동")
        except Exception:
            pass

    def _step_base(self, var: ctk.StringVar, delta: int):
        try:
            bases = [str(b) for b in T.BASES]
            cur = str(var.get())
            if cur not in bases: cur = bases[0]
            i = (bases.index(cur) + delta) % len(bases)
            var.set(bases[i])
            tgt = "출력 진법" if var is self.var_to else "입력 진법"
            self.status.configure(text=f"{tgt} → {bases[i]}")
            self._on_input_changed()
        except Exception:
            pass

    def _shortcut_clear(self):
        self.on_clear()
        self.ent_input.focus_set()
        self.status.configure(text="입력 초기화")

    # ---------------- 입력 보정 & 유효성 ----------------
    _split_re = re.compile(r'([+\-*/()])')

    def _normalize_expr(self, s: str) -> str:
        if not s: return s
        s2 = s.replace(" ", "").replace("_", "").replace(",", "")
        parts = [p for p in self._split_re.split(s2) if p != ""]
        out = []
        for p in parts:
            if p in "+-*/()":
                out.append(p)
            else:
                out.append(p.upper())
        return "".join(out)

    def _iter_number_tokens(self, s: str):
        parts = [p for p in self._split_re.split(s) if p != ""]
        buf = []
        for p in parts:
            if p in "+-*/()":
                if buf:
                    yield "".join(buf)
                    buf = []
            else:
                buf.append(p)
        if buf:
            yield "".join(buf)

    def _find_first_invalid(self, s: str, base: int):
        maxch = _max_digit_char(base)
        for tok in self._iter_number_tokens(s):
            if tok.count(".") > 1:
                return (tok, ".", tok.find(".", tok.find(".")+1),
                        "소수점은 한 번만 사용할 수 있어요.")
            for i, ch in enumerate(tok):
                if ch == ".": 
                    continue
                dv = _digval(ch)
                if dv < 0 or dv >= base:
                    cond = f"{base}진에서는 '0'~'{maxch}'만 사용 가능해요."
                    return (tok, ch, i, cond)
        return None

    def _on_input_changed(self, event=None):
        expr_raw = self.var_input.get()
        try:
            base_from = int(self.var_from.get())
        except Exception:
            base_from = 10
        normalized = self._normalize_expr(expr_raw)
        invalid = self._find_first_invalid(normalized, base_from)
        if invalid:
            tok, ch, idx, cond = invalid
            self.status.configure(text=f"⚠ 유효하지 않은 문자 '{ch}' (토큰: {tok}) — {cond}")
            self._flash_border(self.ent_input, color="#D24747", width=2, ms=140)
        else:
            if normalized != expr_raw and expr_raw.strip():
                self.status.configure(text="(보정 예정: 공백/구분자 제거 & 대문자화)")
            else:
                self.status.configure(text="")

    # ---------------- Big number / wrap / polynomial ----------------
    def _wrap_str(self, s: str) -> str:
        w = self.var_wrap.get()
        if w == "없음": 
            return s
        try:
            width = int(w)
        except:
            return s
        if width <= 0: 
            return s
        sign = ""
        if s.startswith("-"):
            sign, s = "-", s[1:]
        if "." in s:
            intp, frac = s.split(".", 1)
        else:
            intp, frac = s, ""
        def chunk(t):
            return "\n".join(t[i:i+width] for i in range(0, len(t), width)) if t else ""
        intp_w = chunk(intp)
        frac_w = chunk(frac)
        return sign + (intp_w if frac=="" else (intp_w + "." + frac_w))

    def _poly_from_binary(self, b: str) -> str:
        s = b.strip().upper()
        if s.startswith("-"): s = s[1:]
        if "." in s: s = s.split(".", 1)[0]
        if not s: return "0"
        s = s.lstrip("0")
        if not s: return "0"
        deg = len(s) - 1
        terms = []
        for i, ch in enumerate(s):
            if ch != "1": 
                continue
            power = deg - i
            if power == 0:
                terms.append("1")
            elif power == 1:
                terms.append("x")
            else:
                terms.append(f"x^{power}")
        return " + ".join(terms) if terms else "0"

    # ---------------- 연산 트레이스(표시 전용) ----------------
    def _tokenize(self, expr: str):
        # 숫자(소수점 포함)와 연산자/괄호 분리
        tokens = []
        buf = ""
        def flush():
            nonlocal buf
            if buf != "":
                tokens.append(buf)
                buf = ""
        for ch in expr:
            if ch in "+-*/()":
                flush()
                tokens.append(ch)
            else:
                buf += ch
        flush()
        return tokens

    def _precedence(self, op: str) -> int:
        if op in ("*", "/"): return 2
        if op in ("+", "-"): return 1
        return 0

    def _is_operator(self, t: str) -> bool:
        return t in "+-*/"

    def _trace_shunting_yard(self, tokens):
        """셔닝 야드 트레이스: 각 단계에서 (토큰, op스택, out큐) 문자열 반환"""
        output = []
        ops = []
        steps = []
        for t in tokens:
            if self._is_operator(t):
                while ops and self._is_operator(ops[-1]) and self._precedence(ops[-1]) >= self._precedence(t):
                    output.append(ops.pop())
                ops.append(t)
            elif t == "(":
                ops.append(t)
            elif t == ")":
                while ops and ops[-1] != "(":
                    output.append(ops.pop())
                if ops and ops[-1] == "(":
                    ops.pop()
            else:
                # 숫자
                output.append(t)
            steps.append(f"토큰: {t:>2} | 스택: {ops} | 출력: {output}")
        while ops:
            output.append(ops.pop())
            steps.append(f"토큰: (끝) | 스택: {ops} | 출력: {output}")
        return steps, output

    def _trace_postfix_eval(self, postfix):
        """후위표기 평가 트레이스(표시 전용): 중간 값은 기호식으로 축약"""
        st = []
        steps = []
        for t in postfix:
            if self._is_operator(t):
                if len(st) < 2:
                    steps.append(f"오류: 스택 언더플로우 at '{t}'")
                    break
                b = st.pop(); a = st.pop()
                expr = f"({a}{t}{b})"
                st.append(expr)
                steps.append(f"적용 {t}: push {expr} | 스택: {st}")
            else:
                st.append(t)
                steps.append(f"push {t} | 스택: {st}")
        if len(st) == 1:
            steps.append(f"최종: {st[0]}")
        else:
            steps.append(f"최종 스택: {st}")
        return steps

    # ---------------- Events ----------------
    def on_swap(self):
        f, t = self.var_from.get(), self.var_to.get()
        self.var_from.set(t); self.var_to.set(f)
        self._on_input_changed()

    def on_clear(self):
        self.var_input.set("")
        self.var_result.set("")
        for e in (self.sum2, self.sum8, self.sum10, self.sum16):
            e.configure(state="normal"); e.delete(0, END); e.configure(state="readonly")
        self._init_hint()
        self.poly_frame.grid_remove()
        self.status.configure(text="")

    def on_hist_load(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        item = self.hist.get(idx)
        if not item: return
        self.var_input.set(item.expr)
        self.var_from.set(str(item.base_from))
        self.var_to.set(str(item.base_to))
        self._recompute_view(add_history=False)
        self.status.configure(text="히스토리에서 불러옴")

    def del_selected(self):
        sel = self.tree.selection()
        if not sel: return
        self.hist.remove(int(sel[0]))
        self._hist_refresh()
        self.status.configure(text="기록 삭제됨")

    def clear_hist(self):
        if messagebox.askyesno("확인", "정말 전체 기록을 삭제할까요?"):
            self.hist.clear()
            self._hist_refresh()
            self.status.configure(text="전체 기록 삭제됨")

    def on_convert(self):
        self._recompute_view(add_history=True)

    # 핵심: 전체 화면 갱신(연산 트레이스 포함)
    def _recompute_view(self, add_history: bool):
        expr_raw = self.var_input.get().strip()
        try:
            base_from = int(self.var_from.get()); base_to = int(self.var_to.get())
        except Exception:
            messagebox.showerror("오류", "진법 선택이 잘못되었습니다."); return
        if not expr_raw:
            messagebox.showerror("오류", "입력 값이 비어 있습니다."); return

        # 보정 & 유효성
        expr = self._normalize_expr(expr_raw)
        invalid = self._find_first_invalid(expr, base_from)
        if invalid:
            tok, ch, idx, cond = invalid
            self._flash_border(self.ent_input, color="#D24747", width=3, ms=220)
            messagebox.showerror("입력 오류",
                f"입력에 허용되지 않는 문자가 있습니다.\n\n"
                f"문제 토큰: {tok}\n문제 문자: '{ch}' (index {idx})\n사유: {cond}")
            return

        is_expr = bool(re.search(r"[+\-*/()]", expr))
        self.lbl_steps.configure(text=("계산 과정" if is_expr else "변환 과정"))

        # 변환(최종 값 계산은 기존 converter 사용)
        try:
            out, steps = convert(expr, base_from, base_to)
        except Exception as e:
            messagebox.showerror("변환 실패", f"{T.ERR_INVALID}\n\n{e}"); return

        # 정밀도/반올림
        prec = self._get_precision()
        rmode = self.var_rmode.get()
        out_rounded = self._apply_rounding(out, base_to, prec, rmode)

        # 줄바꿈 적용
        out_disp = self._wrap_str(out_rounded)
        self.var_result.set(out_disp)
        self._copy_and_flash(out_rounded)

        # 과정 + 옵션 + (연산 트레이스)
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        if expr != expr_raw:
            self.txt_steps.insert("end", f"[입력 보정] '{expr_raw}' → '{expr}'\n")
        for s in steps:
            self.txt_steps.insert("end", s + "\n")
        self.txt_steps.insert("end", f"\n[정밀도: {prec}, 모드: {rmode}, 줄바꿈: {self.var_wrap.get()}]\n")

        if is_expr and self.var_show_trace.get():
            self.txt_steps.insert("end", "\n— 연산 트레이스 —\n")
            toks = self._tokenize(expr)
            self.txt_steps.insert("end", f"토큰: {toks}\n")
            sy_steps, postfix = self._trace_shunting_yard(toks)
            self.txt_steps.insert("end", "셔닝 야드 단계:\n")
            for ln in sy_steps:
                self.txt_steps.insert("end", f"  {ln}\n")
            self.txt_steps.insert("end", f"\n후위표기: {postfix}\n")
            ev_steps = self._trace_postfix_eval(postfix)
            self.txt_steps.insert("end", "후위표기 평가:\n")
            for ln in ev_steps:
                self.txt_steps.insert("end", f"  {ln}\n")

        self.txt_steps.configure(state="disabled")

        # 요약(2/8/10/16)
        try:
            if is_expr: dec, _ = evaluate_expression(expr, base_from)
            else: dec, _ = to_decimal(expr, base_from)
            b2, _ = from_decimal(dec, 2);   b2 = self._apply_rounding(b2, 2, prec, rmode);   b2 = self._wrap_str(b2)
            b8, _ = from_decimal(dec, 8);   b8 = self._apply_rounding(b8, 8, prec, rmode);   b8 = self._wrap_str(b8)
            b10 = f"{dec}";                 b10 = self._apply_rounding(b10 if "." in b10 else b10 + ".0", 10, prec, rmode).rstrip(".0"); b10 = self._wrap_str(b10)
            b16, _ = from_decimal(dec, 16); b16 = self._apply_rounding(b16, 16, prec, rmode); b16 = self._wrap_str(b16)
            for entry, val in ((self.sum2, b2), (self.sum8, b8), (self.sum10, b10), (self.sum16, b16)):
                entry.configure(state="normal"); entry.delete(0, END); entry.insert(0, val.replace("\n"," ")); entry.configure(state="readonly")
        except Exception:
            pass

        # 다항식 (옵션, 2진 기준)
        try:
            if self.var_poly.get():
                b2_full, _ = from_decimal(dec, 2)
                poly = self._poly_from_binary(b2_full)
                self._show_poly(poly)
            else:
                self.poly_frame.grid_remove()
        except Exception:
            self.poly_frame.grid_remove()

        # 히스토리
        if add_history:
            self.hist.add(expr, base_from, base_to, out_rounded)
            self._hist_refresh()
        self.status.configure(text="완료")

    def _show_poly(self, poly_text: str):
        self.poly_frame.grid()
        self.txt_poly.configure(state="normal")
        self.txt_poly.delete("1.0", "end")
        self.txt_poly.insert("end", poly_text if poly_text else "0")
        self.txt_poly.configure(state="disabled")

    # ---------------- Rounding helpers ----------------
    def _get_precision(self) -> int:
        try:
            p = int(self.var_prec.get())
            return max(0, min(64, p))
        except Exception:
            return 8

    def _apply_rounding(self, s: str, base: int, prec: int, mode: str) -> str:
        sign = ""
        if s.startswith("-"):
            sign, s = "-", s[1:]
        if "." not in s:
            intp, frac = s, ""
        else:
            intp, frac = s.split(".", 1)

        if prec == 0:
            needs_inc = False
            if mode == "round":
                needs_inc = self._should_round_up(frac[:1], frac[1:], base, positive=(sign==""))
            elif mode == "ceil":
                needs_inc = (frac != "" and sign == "")
            elif mode == "floor":
                needs_inc = (frac != "" and sign == "-")
            if needs_inc:
                intp = self._inc_base_str(intp, base)
            return sign + intp

        if len(frac) <= prec:
            return sign + intp + ("." + frac if frac else "")

        keep = frac[:prec]
        drop_head = frac[prec:prec+1]
        drop_tail = frac[prec+1:]

        if mode == "round":
            up = self._should_round_up(drop_head, drop_tail, base, positive=(sign==""))
        elif mode == "ceil":
            up = (sign == "" and (drop_head and drop_head != "0" or any(c != "0" for c in drop_tail)))
        elif mode == "floor":
            up = (sign == "-" and (drop_head and drop_head != "0" or any(c != "0" for c in drop_tail)))
        else:
            up = False

        if up:
            keep, carry = self._inc_frac(keep, base)
            if carry:
                intp = self._inc_base_str(intp, base)

        return sign + intp + "." + keep

    def _should_round_up(self, first_drop: str, rest: str, base: int, positive: bool=True) -> bool:
        if not first_drop:
            return False
        th = (base + 1) // 2  # half-up
        d = _digval(first_drop)
        if d > th: return True
        if d < th: return False
        return True

    def _inc_frac(self, frac_keep: str, base: int):
        if not frac_keep:
            return "", True
        arr = list(frac_keep)
        i = len(arr) - 1
        carry = True
        while i >= 0 and carry:
            v = _digval(arr[i]) + 1
            if v >= base:
                arr[i] = _DIGITS[0]
                carry = True
                i -= 1
            else:
                arr[i] = _DIGITS[v]
                carry = False
        return "".join(arr), carry

    def _inc_base_str(self, intp: str, base: int) -> str:
        if intp == "": intp = "0"
        arr = list(intp)
        i = len(arr) - 1
        carry = True
        while i >= 0 and carry:
            v = _digval(arr[i]) + 1
            if v >= base:
                arr[i] = _DIGITS[0]
                carry = True
                i -= 1
            else:
                arr[i] = _DIGITS[v]
                carry = False
        if carry:
            arr.insert(0, _DIGITS[1])
        return "".join(arr)

    # ---------------- Style & misc ----------------
    def _style_treeview(self):
        style = ttk.Style()
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            bg, fg = "#1f1f1f", "#eaeaea"; sel_bg, sel_fg = "#3a7ebf", "#ffffff"
            hdr_bg, hdr_fg = "#262626", "#eaeaea"
        else:
            bg, fg = "#ffffff", "#222222"; sel_bg, sel_fg = "#cde4ff", "#000000"
            hdr_bg, hdr_fg = "#f2f2f2", "#222222"
        style.theme_use("default")
        style.configure("Treeview", background=bg, foreground=fg,
                        fieldbackground=bg, borderwidth=0, rowheight=24)
        style.map("Treeview", background=[("selected", sel_bg)], foreground=[("selected", sel_fg)])
        style.configure("Treeview.Heading", background=hdr_bg, foreground=hdr_fg, relief="flat")
        style.map("Treeview.Heading", background=[("active", hdr_bg)])

    def _init_sash_positions(self, pw: tk.PanedWindow):
        total = pw.winfo_width()
        if total > 1:
            pw.sash_place(0, int(total * 0.34), 1)
            pw.sash_place(1, int(total * 0.68), 1)

    def _init_hint(self):
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        self.txt_steps.insert("end", T.HINT)
        self.txt_steps.configure(state="disabled")