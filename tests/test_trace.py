from radixscope.core import ExactValue, trace_text, trace_value


def test_integer_conversion_trace() -> None:
    trace = trace_value(ExactValue(13), 2)

    assert trace.result == "1101"
    assert [(step.dividend, step.quotient, step.remainder) for step in trace.integer_steps] == [
        (13, 6, 1),
        (6, 3, 0),
        (3, 1, 1),
        (1, 0, 1),
    ]
    assert trace.fractional_steps == ()
    assert trace.terminates


def test_finite_fraction_conversion_trace() -> None:
    trace = trace_text("A.F", 16, 2)

    assert trace.value == ExactValue(175, 16)
    assert trace.result == "1010.1111"
    assert [step.digit for step in trace.fractional_steps] == ["1", "1", "1", "1"]
    assert trace.recurring_start is None


def test_recurring_fraction_conversion_trace() -> None:
    trace = trace_value(ExactValue(1, 6), 10)

    assert trace.result == "0.1(6)"
    assert [step.digit for step in trace.fractional_steps] == ["1", "6"]
    assert trace.recurring_start == 1
    assert not trace.terminates


def test_negative_trace_keeps_sign_separate() -> None:
    trace = trace_value(ExactValue(-5, 2), 2)

    assert trace.sign == -1
    assert trace.result == "-10.1"
    assert trace.integer_steps[0].dividend == 2
