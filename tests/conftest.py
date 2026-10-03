import os

import pytest
from PySide6.QtWidgets import QApplication

from radixscope.gui.app import create_application

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qt_app() -> QApplication:
    return create_application()
