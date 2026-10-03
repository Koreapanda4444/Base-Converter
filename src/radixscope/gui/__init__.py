import sys


def main() -> int:
    try:
        from radixscope.gui.app import run
    except ModuleNotFoundError as error:
        if error.name and error.name.startswith("PySide6"):
            print(
                'Install the desktop interface with: python -m pip install ".[gui]"',
                file=sys.stderr,
            )
            return 2
        raise
    return run()


__all__ = ["main"]
