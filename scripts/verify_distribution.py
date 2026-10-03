import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from zipfile import ZipFile


def invoke(
    arguments: list[str], directory: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, cwd=directory, env=environment, capture_output=True,
        text=True, encoding="utf-8", check=True, timeout=180,
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    wheel = root / "dist" / "radixscope-2.0.0-py3-none-any.whl"
    archive = root / "dist" / "radixscope-2.0.0.tar.gz"
    with ZipFile(wheel) as package:
        names = package.namelist()
        assert "radixscope/py.typed" in names
        assert "radixscope/gui/app.py" in names
        assert "radixscope/core/ieee754.py" in names
    with tarfile.open(archive, "r:gz") as source:
        names = source.getnames()
        assert "radixscope-2.0.0/docs/install.md" in names
        assert "radixscope-2.0.0/docs/releases/2.0.0.md" in names
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    with tempfile.TemporaryDirectory(prefix="radixscope-install-") as directory:
        temporary = Path(directory)
        target = temporary / "venv"
        invoke([sys.executable, "-m", "venv", str(target)], temporary, environment)
        binary = target / ("Scripts" if os.name == "nt" else "bin")
        python = binary / ("python.exe" if os.name == "nt" else "python")
        cli = binary / ("radixscope.exe" if os.name == "nt" else "radixscope")
        gui = binary / ("radixscope-gui.exe" if os.name == "nt" else "radixscope-gui")
        invoke(
            [str(python), "-m", "pip", "install", "--no-deps", str(wheel)],
            temporary, environment,
        )
        version = invoke([str(cli), "--version"], temporary, environment)
        assert version.stdout.strip() == "RadixScope 2.0.0"
        converted = invoke(
            [str(cli), "convert", "FF", "--from", "16", "--to", "10", "--json"],
            temporary, environment,
        )
        assert json.loads(converted.stdout)["outputs"] == {"10": "255"}
        missing_gui = subprocess.run(
            [str(gui)], cwd=temporary, env=environment, capture_output=True,
            text=True, encoding="utf-8", check=False, timeout=30,
        )
        assert missing_gui.returncode == 2 and "[gui]" in missing_gui.stderr
        invoke([str(python), "-m", "pip", "install", f"{wheel}[gui]"], temporary, environment)
        code = (
            "from PySide6.QtCore import QTimer; "
            "from radixscope.gui.app import create_application; "
            "from radixscope.gui import main; "
            "app = create_application(); "
            "QTimer.singleShot(100, app.quit); "
            "assert main() == 0"
        )
        invoke([str(python), "-c", code], temporary, environment)
    print("Wheel/source contents, isolated CLI installation and installed GUI startup passed")


if __name__ == "__main__":
    main()
