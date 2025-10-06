# gui/main.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 상위(Base-Converter) 경로 추가

from gui.ui import App

if __name__ == "__main__":
    App().mainloop()
