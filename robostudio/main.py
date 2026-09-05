#!/usr/bin/env python3
"""
RoboStudio MVP - Entry Point
"""

import sys
from pathlib import Path

# Keep the repository root importable when RoboStudio is launched directly
# (`python robostudio/main.py`) or imported by the test runner. Shared tools
# such as tools.bootstrap_config live at repository scope.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from app import RoboStudioApp
from ui.robot_tab import RobotTab


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RoboStudio")
    app.setOrganizationName("RobotDevPlatform")

    window = RoboStudioApp()
    robot_tab = RobotTab(lambda: window.ui.code_editor.toPlainText(), window)
    window.ui.main_tabs.addTab(robot_tab, "Robot")
    window.ui.code_editor.textChanged.connect(robot_tab.refresh_code_state)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
