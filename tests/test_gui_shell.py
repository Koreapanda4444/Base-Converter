from PySide6.QtWidgets import QApplication

from radixscope.gui.app import MainWindow, create_application


def test_desktop_shell_has_four_accessible_workspaces(qt_app: QApplication) -> None:
    window = MainWindow()
    window.show()
    qt_app.processEvents()
    assert window.isVisible()
    assert window.tabs.count() == 4
    assert [window.tabs.tabText(i) for i in range(4)] == [
        "Conversion", "Trace", "Programmer", "IEEE 754"
    ]
    assert all(workspace.output.isReadOnly() for workspace in window.workspaces)
    window.actions()[3].trigger()
    assert window.tabs.currentIndex() == 3
    window.close()


def test_result_error_and_clipboard_flow(qt_app: QApplication) -> None:
    window = MainWindow()
    workspace = window.workspaces[0]
    workspace.set_result({"exact": "255", "outputs": {"16": "FF"}})
    assert "FF" in workspace.output.toPlainText()
    assert window.statusBar().currentMessage() == "Conversion complete"
    workspace.copy_button.click()
    assert QApplication.clipboard().text() == workspace.output.toPlainText()
    workspace.set_error("Invalid digit")
    assert workspace.error.text() == "Invalid digit"
    assert workspace.output.toPlainText() == ""
    assert qt_app is create_application()
    window.close()
