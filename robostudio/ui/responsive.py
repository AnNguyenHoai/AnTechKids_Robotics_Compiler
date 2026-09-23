"""Shared responsive layout primitives for RoboStudio.

Phase 1 keeps business behaviour unchanged and centralises the geometry policy so
individual screens do not invent their own resize thresholds.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QScrollArea, QSplitter, QWidget


class LayoutMode(str, Enum):
    NARROW = "narrow"
    COMPACT = "compact"
    WIDE = "wide"


# Window/content breakpoints are intentionally centralised.  They are not a
# visual-design contract; they are the Phase-1 usability thresholds used to
# prevent controls from competing for impossible horizontal space.
NARROW_MAX_WIDTH = 899
WIDE_MIN_WIDTH = 1200
SPLITTER_WIDE_MIN_WIDTH = 1080


def layout_mode_for_width(width: int) -> LayoutMode:
    if width <= NARROW_MAX_WIDTH:
        return LayoutMode.NARROW
    if width < WIDE_MIN_WIDTH:
        return LayoutMode.COMPACT
    return LayoutMode.WIDE


def make_scroll_area(widget: QWidget) -> QScrollArea:
    """Return a frameless, vertically scrolling responsive container."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    area.setWidget(widget)
    return area


class AdaptiveSplitter(QSplitter):
    """Horizontal when enough room exists; vertical when space becomes compact."""

    mode_changed = Signal(str)

    def __init__(self, parent=None, *, wide_min_width: int = SPLITTER_WIDE_MIN_WIDTH):
        super().__init__(Qt.Horizontal, parent)
        self._wide_min_width = int(wide_min_width)
        self._last_wide = True
        self.setChildrenCollapsible(False)
        self.setHandleWidth(6)

    @property
    def is_wide(self) -> bool:
        return self.orientation() == Qt.Horizontal

    def apply_width(self, width: int) -> None:
        wide = int(width) >= self._wide_min_width
        if wide == self._last_wide and self.orientation() == (Qt.Horizontal if wide else Qt.Vertical):
            return
        self._last_wide = wide
        self.setOrientation(Qt.Horizontal if wide else Qt.Vertical)
        count = max(1, self.count())
        if wide:
            # Console/log content benefits from a little more horizontal room.
            if count == 2:
                self.setSizes([440, 620])
            else:
                self.setSizes([1] * count)
        else:
            self.setSizes([1] * count)
        self.mode_changed.emit("wide" if wide else "stacked")

    def resizeEvent(self, event) -> None:
        self.apply_width(event.size().width())
        super().resizeEvent(event)
