#!/usr/bin/env python3
"""
RoboStudio MVP - Entry Point
"""

import sys
from pathlib import Path

# Bootstrap before importing PySide6 or application services. In frozen mode
# PyInstaller may place Python modules under _internal/_MEIPASS while the
# writable/distributed runtime lives beside the launched executable.
if getattr(sys, "frozen", False):
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    if str(bundle_root) not in sys.path:
        sys.path.insert(0, str(bundle_root))
else:
    # Keep the repository root importable when RoboStudio is launched directly
    # (`python robostudio/main.py`) or imported by the test runner. Shared tools
    # such as tools.bootstrap_config live at repository scope.
    bundle_root = Path(__file__).resolve().parents[1]
    if str(bundle_root) not in sys.path:
        sys.path.insert(0, str(bundle_root))

from tools.runtime_bootstrap import bootstrap

# A packaged executable must never start against a partial runtime. Source
# development keeps the historical non-frozen behavior; RSD-06 validates the
# application-owned distribution before the GUI imports any services.
bootstrap(validate_runtime=True)

from PySide6.QtWidgets import QApplication
from app import RoboStudioApp
from ui.responsive_robot_tab import ResponsiveRobotTab as RobotTab


ACCEPTANCE_PROBE_ARG = "--acceptance-probe"


def main() -> int:
    # B2.5 needs a bounded, non-interactive way to prove that the *packaged GUI
    # application itself* can initialize on an independent clean machine.  The
    # probe constructs the real window/Robot tab and processes Qt events, but it
    # does not enter the indefinite GUI event loop.  Normal launches are
    # unchanged and still use app.exec().
    acceptance_probe = ACCEPTANCE_PROBE_ARG in sys.argv
    qt_argv = [arg for arg in sys.argv if arg != ACCEPTANCE_PROBE_ARG]

    app = QApplication(qt_argv)
    app.setApplicationName("RoboStudio")
    app.setOrganizationName("RobotDevPlatform")

    window = RoboStudioApp()
    robot_tab = RobotTab(lambda: window.ui.code_editor.toPlainText(), window)
    window.ui.main_tabs.addTab(robot_tab, "Robot")
    window.ui.code_editor.textChanged.connect(robot_tab.refresh_code_state)

    if acceptance_probe:
        window.show()
        app.processEvents()
        window.close()
        app.processEvents()
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
