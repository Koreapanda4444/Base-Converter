from PySide6.QtCore import Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from radixscope.reports import render_report


class Workspace(QWidget):
    result_ready = Signal(str, dict)

    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        self.title = title
        self.form = QFormLayout()
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.output.setAccessibleName(f"{title} result")
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setObjectName("error")
        self.run_button = QPushButton("Run")
        self.run_button.setEnabled(False)
        self.copy_button = QPushButton("Copy result")
        self.copy_button.clicked.connect(self.copy_result)
        actions = QHBoxLayout()
        actions.addWidget(self.run_button)
        actions.addStretch()
        actions.addWidget(self.copy_button)
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("heading")
        subtitle = QLabel(description)
        subtitle.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        layout.addLayout(self.form)
        layout.addLayout(actions)
        layout.addWidget(self.error)
        layout.addWidget(self.output, 1)

    def set_result(self, report: dict[str, object]) -> None:
        self.error.clear()
        self.output.setPlainText(render_report(report))
        self.result_ready.emit(self.title, report)

    def set_error(self, message: str) -> None:
        self.output.clear()
        self.error.setText(message)

    def copy_result(self) -> None:
        QApplication.clipboard().setText(self.output.toPlainText())
