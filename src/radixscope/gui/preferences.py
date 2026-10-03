from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from radixscope.settings import SettingsStore


class PreferencesDialog(QDialog):
    def __init__(self, store: SettingsStore, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.theme = QComboBox()
        self.theme.addItems(["System", "Light", "Dark"])
        theme = store.preferences.get("theme", "System")
        if isinstance(theme, str) and self.theme.findText(theme) >= 0:
            self.theme.setCurrentText(theme)
        self.remember = QCheckBox("Keep recent history")
        self.remember.setChecked(store.remember_history)
        self.limit = QSpinBox()
        self.limit.setRange(1, 100)
        self.limit.setValue(store.history_limit)
        form = QFormLayout()
        form.addRow("Theme", self.theme)
        form.addRow("Recent history", self.remember)
        form.addRow("Maximum entries", self.limit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
