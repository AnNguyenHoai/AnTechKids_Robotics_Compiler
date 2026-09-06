"""H28-A smoke tests for RoboStudio USB serial console integration."""
from __future__ import annotations

import os
import sys


# Keep Qt tests headless on CI and developer machines without a display.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    robostudio_dir = os.path.join(repo_root, "robostudio")
    sys.path.insert(0, robostudio_dir)

    from PySide6.QtWidgets import QApplication
    from services.serial_console_service import DEFAULT_BAUD_RATE, SerialConsoleService
    from ui.serial_console import SerialConsoleWidget

    assert DEFAULT_BAUD_RATE == 115200
    assert isinstance(SerialConsoleService.available_ports(), list)

    app = QApplication.instance() or QApplication([])
    widget = SerialConsoleWidget()
    widget.append_output("line 1\n")
    widget.append_output("line 2\n")
    assert widget.output.toPlainText() == "line 1\nline 2\n"

    widget.clear()
    assert widget.output.toPlainText() == ""
    widget.close()
    app.processEvents()

    print("H28-A RoboStudio Serial Console smoke test: PASS")


if __name__ == "__main__":
    main()
