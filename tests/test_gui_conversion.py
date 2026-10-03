import pytest
from PySide6.QtWidgets import QApplication

from radixscope.core import ExactValue, trace_value
from radixscope.gui.conversion import ConversionWorkspace, TraceWorkspace


def test_conversion_and_expression_controls(qt_app: QApplication) -> None:
    workspace = ConversionWorkspace()
    workspace.input.setText("FF")
    workspace.source_base.setValue(16)
    workspace.run_button.click()
    assert "exact: 255" in workspace.output.toPlainText()
    assert "16: FF" in workspace.output.toPlainText()
    workspace.mode.setCurrentText("Expression")
    assert not workspace.source_base.isEnabled()
    workspace.input.setText("0x10 + 2#11 / 10#2")
    workspace.run_button.click()
    assert "exact: 35/2" in workspace.output.toPlainText()
    workspace.input.setText("1/0")
    workspace.run_button.click()
    assert workspace.error.text() and workspace.output.toPlainText() == ""
    workspace.close()


def test_rounding_and_duplicate_target_errors(qt_app: QApplication) -> None:
    workspace = ConversionWorkspace()
    workspace.input.setText("1/8")
    workspace.targets.setText("10")
    workspace.exact_output.setChecked(False)
    workspace.precision.setValue(2)
    assert workspace.precision.isEnabled()
    workspace.rounding.setCurrentText("half-up")
    workspace.run_button.click()
    assert "10: 0.13" in workspace.output.toPlainText()
    workspace.targets.setText("2, 2")
    workspace.run_button.click()
    assert "unique" in workspace.error.text()
    workspace.close()


def test_trace_reports_partial_output_and_recurring_cycle(qt_app: QApplication) -> None:
    workspace = TraceWorkspace()
    workspace.run_button.click()
    assert "result: 0.(01)" in workspace.output.toPlainText()
    workspace.limit.setValue(1)
    workspace.run_button.click()
    assert "complete: False" in workspace.output.toPlainText()
    assert "result: 0.0\u2026" in workspace.output.toPlainText()
    workspace.input.setText("bad")
    workspace.run_button.click()
    assert workspace.error.text()
    workspace.close()


def test_bounded_trace_distinguishes_partial_terminated_and_recurring() -> None:
    partial = trace_value(ExactValue(-22, 7), 10, max_steps=2)
    assert partial.value == ExactValue(-22, 7)
    assert partial.result == "-3.14\u2026"
    assert not partial.complete and not partial.terminates
    terminated = trace_value(ExactValue(1, 2), 10, max_steps=1)
    assert terminated.complete and terminated.terminates
    recurring = trace_value(ExactValue(1, 3), 10, max_steps=1)
    assert recurring.complete and not recurring.terminates
    for limit in (0, -1, True):
        with pytest.raises(ValueError):
            trace_value(ExactValue(1, 7), 10, max_steps=limit)
