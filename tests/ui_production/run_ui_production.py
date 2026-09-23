#!/usr/bin/env python3
"""RoboStudio Phase-2 production UX contract gate."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[2]
ROBOSTUDIO = ROOT / "robostudio"
for path in (str(ROOT), str(ROBOSTUDIO)):
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtWidgets import QApplication

from ui.components import StatusBadge
from ui.first_flash_dialog import FirstFlashSetupDialog
from ui.responsive_robot_tab import ResponsiveRobotTab


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def test_setup_flow(app: QApplication) -> None:
    events: list[str] = []
    dialog = FirstFlashSetupDialog(
        on_refresh_usb=lambda: events.append("refresh"),
        on_flash=lambda: events.append("flash"),
    )
    check("first-flash flow has two user steps", dialog.stack.count() == 2)
    check("first-flash starts on network step", dialog.stack.currentIndex() == 0)
    check("bootstrap generation is not exposed as a user action", dialog.generate_compat_button.isHidden())
    dialog.next_button.click()
    app.processEvents()
    check("Continue advances to USB step", dialog.stack.currentIndex() == 1)
    check("USB step refreshes device inventory", events == ["refresh"])
    dialog.flash_button.setEnabled(True)
    dialog.flash_button.click()
    app.processEvents()
    check("Flash Robot maps to one deployment action", events[-1] == "flash")
    dialog.close()
    dialog.deleteLater()


def test_semantic_status() -> None:
    badge = StatusBadge("Ready", "success")
    check("status badge carries text semantics", badge.text() == "Ready")
    check("status badge carries semantic tone", badge.property("tone") == "success")
    badge.set_status("Offline", "neutral")
    check("status badge can transition without replacement", badge.text() == "Offline")
    badge.deleteLater()


def test_robot_golden_path(app: QApplication) -> None:
    with tempfile.TemporaryDirectory(prefix="robostudio-ui-phase2-") as temp:
        old_state = os.environ.get("ROBOSTUDIO_STATE_ROOT")
        os.environ["ROBOSTUDIO_STATE_ROOT"] = str(Path(temp) / "state")
        try:
            tab = ResponsiveRobotTab(lambda: "print('student program')")
            check("Robot workspace exposes Setup New Robot secondary action", tab.setup_robot_button.text().endswith("Setup New Robot"))
            check("robot details are collapsed by default", tab.robot_details.isHidden())
            check("diagnostics are tabs instead of simultaneous panes", tab.diagnostics_tabs.count() == 2)
            check("Serial Console is an on-demand diagnostics tab", tab.diagnostics_tabs.tabText(0) == "Serial Console")
            check("Deployment Log is an on-demand diagnostics tab", tab.diagnostics_tabs.tabText(1) == "Deployment Log")
            check("first-flash implementation detail remains outside golden path", not tab.generate_bootstrap_button.isVisible())
            tab.close()
            tab.deleteLater()
            app.processEvents()
        finally:
            if old_state is None:
                os.environ.pop("ROBOSTUDIO_STATE_ROOT", None)
            else:
                os.environ["ROBOSTUDIO_STATE_ROOT"] = old_state


def test_navigation_and_program_hierarchy() -> None:
    main_text = (ROOT / "robostudio" / "main.py").read_text(encoding="utf-8")
    window_text = (ROOT / "robostudio" / "ui" / "main_window.py").read_text(encoding="utf-8")
    check("Robot is the second primary navigation tab", 'insertTab(1, robot_tab, "Robot")' in main_text)
    check("technical firmware action moved to Advanced menu", 'self.advanced_menu = menubar.addMenu("&Advanced")' in window_text)
    check("legacy firmware button is hidden from primary Program flow", "self.open_firmware_button.setVisible(False)" in window_text)
    check("Program readiness details are collapsed by default", "self.capability_details.setVisible(False)" in window_text)
    check("target readiness details are collapsed by default", "self.target_capability_details.setVisible(False)" in window_text)


def main() -> int:
    app = QApplication.instance() or QApplication([])
    test_setup_flow(app)
    test_semantic_status()
    test_robot_golden_path(app)
    test_navigation_and_program_hierarchy()
    app.processEvents()
    print("RoboStudio Phase-2 production UX: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
