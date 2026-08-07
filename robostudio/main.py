#!/usr/bin/env python3
"""
RoboStudio MVP - Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication
from app import RoboStudioApp


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RoboStudio")
    app.setOrganizationName("RobotDevPlatform")

    window = RoboStudioApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()