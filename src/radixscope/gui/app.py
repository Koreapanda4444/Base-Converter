import sys
from functools import partial

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from radixscope import __version__
from radixscope.gui.conversion import ConversionWorkspace, TraceWorkspace
from radixscope.gui.programmer import IEEEWorkspace, ProgrammerWorkspace
from radixscope.gui.widgets import Workspace


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"RadixScope {__version__}")
        self.resize(1000, 720)
        self.setMinimumSize(640, 480)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.workspaces: list[Workspace] = [
            ConversionWorkspace(),
            TraceWorkspace(),
            ProgrammerWorkspace(),
            IEEEWorkspace(),
        ]
        for index, workspace in enumerate(self.workspaces):
            self.tabs.addTab(workspace, workspace.title)
            action = QAction(workspace.title, self)
            action.setShortcut(QKeySequence(f"Ctrl+{index + 1}"))
            action.triggered.connect(partial(self.tabs.setCurrentIndex, index))
            self.addAction(action)
            workspace.result_ready.connect(self.show_completed)
        self.setCentralWidget(self.tabs)
        self.statusBar().showMessage("Ready · Ctrl+1 through Ctrl+4 switch workspaces")
        self.setStyleSheet(
            "QWidget { font-size: 13px; }"
            "QLabel#heading { font-size: 22px; font-weight: 600; margin-top: 8px; }"
            "QLabel#error { color: #d34a4a; }"
            "QPushButton { padding: 7px 14px; }"
            "QLineEdit, QSpinBox, QComboBox { padding: 5px; }"
            "QTabWidget::pane { border: 0; }"
        )

    def show_completed(self, title: str, report: dict[str, object]) -> None:
        self.statusBar().showMessage(f"{title} complete", 5000)


def create_application() -> QApplication:
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    application = QApplication(sys.argv)
    application.setApplicationName("RadixScope")
    application.setOrganizationName("Koreapanda4444")
    application.setApplicationVersion(__version__)
    return application


def run() -> int:
    application = create_application()
    window = MainWindow()
    window.show()
    return application.exec()
