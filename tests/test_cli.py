import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from radixscope import __version__
from radixscope.cli import main


def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    source = Path(__file__).resolve().parents[1] / "src"
    environment["PYTHONPATH"] = str(source) + os.pathsep + environment.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "radixscope", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        timeout=15,
        check=False,
    )


def json_output(*arguments: str) -> dict[str, object]:
    result = invoke(*arguments, "--json")
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    report = json.loads(result.stdout)
    assert isinstance(report, dict)
    return cast(dict[str, object], report)


def test_conversion_preserves_recurring_values_and_base_order() -> None:
    report = json_output("convert", "0.(3)", "--to", "10", "2", "16")
    assert report == {"exact": "1/3", "outputs": {"10": "0.(3)", "2": "0.(01)", "16": "0.(5)"}}
    text = invoke("convert", "FF", "--from", "16", "--to", "2", "10")
    assert text.returncode == 0
    assert text.stdout == "exact: 255\noutputs:\n  2: 11111111\n  10: 255\n"


@pytest.mark.parametrize(
    "mode,expected",
    [("truncate", "0.12"), ("half-even", "0.12"), ("half-up", "0.13"),
     ("floor", "0.12"), ("ceiling", "0.13")],
)
def test_cli_rounding_modes(mode: str, expected: str) -> None:
    report = json_output(
        "convert", "1/8", "--to", "10", "--precision", "2", "--rounding", mode
    )
    assert report["outputs"] == {"10": expected}


def test_expression_is_exact_and_trace_exposes_repetition() -> None:
    report = json_output("expression", "0x10 + 2#11 / 10#2", "--to", "10")
    assert report == {"exact": "35/2", "outputs": {"10": "17.5"}}
    trace = json_output("trace", "1/3", "--to", "2")
    assert trace["result"] == "0.(01)"
    assert trace["recurring_start"] == 0
    assert trace["terminates"] is False
    steps = trace["fractional_steps"]
    assert isinstance(steps, list) and len(steps) == 2
    readable = invoke("trace", "255", "--to", "16")
    assert readable.returncode == 0 and "integer_steps:" in readable.stdout


@pytest.mark.parametrize(
    "operation,operand,expected,exact,overflowed",
    [("add", "1", -128, 128, True), ("subtract", "1", 126, 126, False),
     ("multiply", "2", -2, 254, True)],
)
def test_integer_arithmetic_reports_exact_and_wrapped_results(
    operation: str, operand: str, expected: int, exact: int, overflowed: bool
) -> None:
    report = json_output(
        "integer", "127", "--width", "8", "--signed", "--op", operation, "--operand", operand
    )
    assert report["value"] == expected
    assert report["exact_result"] == exact
    assert report["overflowed"] is overflowed


@pytest.mark.parametrize(
    "operation,operand,expected",
    [("and", "15", 0), ("or", "15", -113), ("xor", "15", -113),
     ("shl", "1", 0), ("shr", "1", -64), ("lshr", "1", 64)],
)
def test_cli_bitwise_operations(operation: str, operand: str, expected: int) -> None:
    report = json_output(
        "integer", "-128", "--width", "8", "--signed", "--op", operation, "--operand", operand
    )
    assert report["value"] == expected
    assert report["width"] == 8 and report["signed"] is True


def test_not_and_pattern_input_preserve_raw_bits_and_endian_order() -> None:
    report = json_output("integer", "0", "--width", "5", "--op", "not")
    assert report["value"] == 31 and report["bits"] == "11111"
    pattern = json_output(
        "integer", "FFFE", "--base", "16", "--width", "16", "--signed", "--pattern",
        "--byteorder", "little",
    )
    assert pattern["value"] == -2
    assert pattern["unsigned"] == 65534
    assert pattern["bytes"] == "FE FF"


def test_ieee_encode_decode_and_signaling_nan() -> None:
    encoded = json_output("ieee", "encode", "1/10", "--width", "32")
    assert encoded["hexadecimal"] == "3DCCCCCD"
    decoded = json_output("ieee", "decode", "3DCCCCCD", "--width", "32")
    assert decoded == encoded
    nan = json_output("ieee", "encode", "nan", "--width", "32", "--payload", "123", "--signaling")
    assert nan["classification"] == "nan"
    assert nan["nan_payload"] == 123 and nan["quiet_nan"] is False
    zero = json_output("ieee", "encode", "0", "--width", "32", "--negative-zero")
    assert zero["hexadecimal"] == "80000000"
    negative_infinity = invoke("ieee", "encode", "--width", "32", "--json", "--", "-inf")
    assert negative_infinity.returncode == 0
    assert json.loads(negative_infinity.stdout)["hexadecimal"] == "FF800000"


@pytest.mark.parametrize(
    "arguments",
    [
        [], ["unknown"], ["convert", "G", "--from", "16"],
        ["convert", "1", "--to", "2", "2"], ["convert", "1", "--precision", "-1"],
        ["expression", "1/0"], ["expression", "__import__('os')"],
        ["integer", "256", "--width", "8"], ["integer", "1", "--width", "0"],
        ["integer", "1", "--op", "and"], ["integer", "1", "--operand", "1"],
        ["integer", "1", "--op", "not", "--operand", "1"],
        ["integer", "1", "--op", "shr", "--operand", "-1"],
        ["ieee", "decode", "100000000", "--width", "32"],
        ["ieee", "decode", "0", "--negative-zero"],
        ["ieee", "encode", "nan", "--signaling"],
        ["ieee", "encode", "inf", "--signaling"],
        ["ieee", "encode", "inf", "--negative-zero"],
        ["ieee", "encode", "1", "--payload", "1"],
        ["ieee", "encode", "--", "--nan"],
    ],
)
def test_invalid_commands_have_no_traceback_or_partial_stdout(arguments: list[str]) -> None:
    result = invoke(*arguments)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr and "Traceback" not in result.stderr


@pytest.mark.parametrize("command", ["", "convert", "expression", "trace", "integer", "ieee"])
def test_help_is_available_for_every_command(command: str) -> None:
    result = invoke(*([command] if command else []), "--help")
    assert result.returncode == 0
    assert "usage:" in result.stdout and result.stderr == ""


def test_version_and_in_process_entry_point(capsys: pytest.CaptureFixture[str]) -> None:
    assert invoke("--version").stdout == f"RadixScope {__version__}\n"
    assert main(["convert", "1010", "--from", "2", "--to", "10", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["outputs"] == {"10": "10"}
    assert main(["convert", "invalid"]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("radixscope:")
