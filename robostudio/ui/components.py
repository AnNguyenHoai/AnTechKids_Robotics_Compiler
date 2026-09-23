"""Reusable Phase-2 presentation components."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QToolButton, QVBoxLayout, QWidget

from ui import theme


class StatusBadge(QLabel):
    """Compact semantic state indicator that does not rely on colour alone."""

    def __init__(self, text: str = "", tone: str = "neutral", parent=None):
        super().__init__(parent)
        self.setObjectName("statusBadge")
        self.setAlignment(Qt.AlignCenter)
        self.set_status(text, tone)

    def set_status(self, text: str, tone: str = "neutral") -> None:
        self.setText(text)
        self.setProperty("tone", tone)
        self.setStyleSheet(theme.badge_style(tone))
        self.adjustSize()


class DisclosureButton(QToolButton):
    """Small details disclosure with predictable expanded/collapsed wording."""

    def __init__(self, label: str = "Details", parent=None):
        super().__init__(parent)
        self._label = label
        self.setCheckable(True)
        self.setChecked(False)
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.toggled.connect(self._sync_text)
        self._sync_text(False)

    def _sync_text(self, expanded: bool) -> None:
        self.setText(("Hide " if expanded else "Show ") + self._label.lower())


class SummaryCard(QFrame):
    """Simple production card with title/content slots."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("summaryCard")
        self.setStyleSheet(theme.card_style())
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(6)
        heading = QLabel(title)
        heading.setStyleSheet(f"font-weight: 700; color: {theme.TEXT_PRIMARY}; border: none;")
        self.layout.addWidget(heading)

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        self.layout.addWidget(widget, stretch)
