# ui.py

import customtkinter as ctk
from constants import Base_options
from logic import calculate, convert_result_to_bases, to_int


class BaseConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("진법 계산기 / 변환기")
        self.geometry("500x550")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.tabview = ctk.CTkTabview(self, width=480)
        self.tabview.pack(pady=20, expand=True)

        self.calculator_tab = self.tabview.add("진법 계산기")
        self.converter_tab = self.tabview.add("진법 변환기")

        self.build_calculator_tab()
        self.build_converter_tab()

    def build_calculator_tab(self):
        self.base1_var = ctk.StringVar(value=Base_options[2])
        self.base2_var = ctk.StringVar(value=Base_options[2])

        ctk.CTkLabel(self.calculator_tab, text="진법 선택").pack(pady=2)
        self.base1_menu = ctk.CTkOptionMenu(self.calculator_tab, values=Base_options, variable=self.base1_var)
        self.base1_menu.pack()

        self.input1 = ctk.CTkEntry(self.calculator_tab, placeholder_text="값 입력")
        self.input1.pack(pady=5)

        self.operator_var = ctk.StringVar(value="+")
        ctk.CTkLabel(self.calculator_tab, text="값 입력").pack(pady=2)
        operator_frame = ctk.CTkFrame(self.calculator_tab)
        operator_frame.pack(pady=5)
        for op in ["+", "-", "×", "÷"]:
            ctk.CTkRadioButton(operator_frame, text=op, variable=self.operator_var, value=op).pack(side="left", padx=5)

        ctk.CTkLabel(self.calculator_tab, text="진법 선택").pack(pady=2)
        self.base2_menu = ctk.CTkOptionMenu(self.calculator_tab, values=Base_options, variable=self.base2_var)
        self.base2_menu.pack()

        self.input2 = ctk.CTkEntry(self.calculator_tab, placeholder_text="값 입력")
        self.input2.pack(pady=5)

        ctk.CTkButton(self.calculator_tab, text="계산하기", command=self.calculate_and_display).pack(pady=10)

        self.result_fields = {}
        for label in Base_options:
            row = ctk.CTkFrame(self.calculator_tab)
            row.pack(pady=2, fill="x", padx=20)
            ctk.CTkLabel(row, text=label, width=60).pack(side="left")

            entry = ctk.CTkEntry(row)
            entry.configure(state="readonly")
            entry.pack(side="left", fill="x", expand=True)
            self.result_fields[label] = entry

    def build_converter_tab(self):
        self.input_base_var = ctk.StringVar(value=Base_options[2])
        ctk.CTkLabel(self.converter_tab, text="진법 선택").pack(pady=2)
        self.input_base_menu = ctk.CTkOptionMenu(self.converter_tab, values=Base_options, variable=self.input_base_var)
        self.input_base_menu.pack()

        self.input_value = ctk.CTkEntry(self.converter_tab, placeholder_text="값 입력")
        self.input_value.pack(pady=5)

        ctk.CTkButton(self.converter_tab, text="변환하기", command=self.convert_and_display).pack(pady=10)

        self.convert_result_fields = {}
        for label in Base_options:
            row = ctk.CTkFrame(self.converter_tab)
            row.pack(pady=2, fill="x", padx=20)
            ctk.CTkLabel(row, text=label, width=60).pack(side="left")

            entry = ctk.CTkEntry(row)
            entry.configure(state="readonly")
            entry.pack(side="left", fill="x", expand=True)
            self.convert_result_fields[label] = entry

    def set_entry_value(self, entry: ctk.CTkEntry, value: str):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value)
        entry.configure(state="readonly")
    def calculate_and_display(self):
        val1 = self.input1.get()
        val2 = self.input2.get()
        base1 = self.base1_var.get()
        base2 = self.base2_var.get()
        operator = self.operator_var.get()

        try:
            result = calculate(val1, val2, base1, base2, operator)
            converted = convert_result_to_bases(result)
            for base in Base_options:
                self.set_entry_value(self.result_fields[base], converted[base])
        except Exception as e:
            for field in self.result_fields.values():
                self.set_entry_value(field, f"오류: {str(e)}")

    def convert_and_display(self):
        val = self.input_value.get()
        base = self.input_base_var.get()

        try:
            num = to_int(val, base)
            converted = convert_result_to_bases(num)
            for b in Base_options:
                self.set_entry_value(self.convert_result_fields[b], converted[b])
        except Exception as e:
            for field in self.convert_result_fields.values():
                self.set_entry_value(field, f"오류: {str(e)}")


def start_ui():
    app = BaseConverterApp()
    app.mainloop()
