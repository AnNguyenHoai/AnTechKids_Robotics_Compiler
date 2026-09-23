"""Phase-1 responsive foundation regression tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[2]
ROBOSTUDIO = ROOT / "robostudio"
for path in (str(ROOT), str(ROBOSTUDIO)):
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.responsive import AdaptiveSplitter, LayoutMode, layout_mode_for_width
from ui.responsive_hardware_tab import ResponsiveHardwareTab
from ui.responsive_serial_console import ResponsiveSerialConsoleWidget


_app = QApplication.instance() or QApplication([])


def test_breakpoint_contract():
    assert layout_mode_for_width(820) == LayoutMode.NARROW
    assert layout_mode_for_width(900) == LayoutMode.COMPACT
    assert layout_mode_for_width(1100) == LayoutMode.COMPACT
    assert layout_mode_for_width(1200) == LayoutMode.WIDE


def test_adaptive_splitter_stacks_when_compact():
    splitter = AdaptiveSplitter(wide_min_width=1080)
    splitter.apply_width(1200)
    assert splitter.orientation() == Qt.Horizontal
    splitter.apply_width(1000)
    assert splitter.orientation() == Qt.Vertical


def test_serial_console_has_no_wide_hard_minimum():
    widget = ResponsiveSerialConsoleWidget()
    # The old toolbar forced a 230 px port combo plus three peers on one row.
    # Phase 1 keeps the combo shrinkable and moves controls to a second row.
    assert widget.port_combo.minimumWidth() <= 120
    assert widget.output.minimumHeight() <= 110
    widget.close()


def test_hardware_tab_is_scrollable():
    widget = ResponsiveHardwareTab()
    assert widget.scroll_area.widgetResizable()
    assert widget.scroll_area.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    widget.close()
