#!/usr/bin/env python3
"""RoboStudio Phase-1 responsive layout contract gate."""
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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from domain.hardware_config_service import HardwareConfigService
from ui.responsive import AdaptiveSplitter, LayoutMode, layout_mode_for_width
from ui.responsive_hardware_tab import ResponsiveHardwareTab
from ui.responsive_serial_console import ResponsiveSerialConsoleWidget


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    app = QApplication.instance() or QApplication([])

    check("820px is narrow", layout_mode_for_width(820) == LayoutMode.NARROW)
    check("960px is compact", layout_mode_for_width(960) == LayoutMode.COMPACT)
    check("1100px is compact", layout_mode_for_width(1100) == LayoutMode.COMPACT)
    check("1200px is wide", layout_mode_for_width(1200) == LayoutMode.WIDE)

    splitter = AdaptiveSplitter(wide_min_width=1080)
    splitter.apply_width(1200)
    check("wide Robot workspace is horizontal", splitter.orientation() == Qt.Horizontal)
    splitter.apply_width(1000)
    check("compact Robot workspace stacks vertically", splitter.orientation() == Qt.Vertical)
    splitter.deleteLater()

    serial = ResponsiveSerialConsoleWidget()
    check("serial COM selector no longer forces 230px", serial.port_combo.minimumWidth() <= 120)
    check("serial output has compact-safe minimum height", serial.output.minimumHeight() <= 110)
    serial.close()
    serial.deleteLater()

    with tempfile.TemporaryDirectory() as temp:
        config_service = HardwareConfigService(Path(temp) / "hardware.json")
        hardware = ResponsiveHardwareTab(config_service=config_service)
        check("Hardware tab is vertically scrollable", hardware.scroll_area.widgetResizable())
        check(
            "Hardware tab forbids application-level horizontal scroll",
            hardware.scroll_area.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff,
        )
        hardware.close()
        hardware.deleteLater()

    app.processEvents()
    print("RoboStudio responsive foundation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
