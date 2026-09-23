"""Responsive Hardware tab presentation built on the existing hardware logic."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from domain.device_registry import DeviceRegistry
from ui.hardware_tab import CATEGORY_TITLES, HardwareTab
from ui.responsive import make_scroll_area


class ResponsiveHardwareTab(HardwareTab):
    """Hardware configuration with vertical scrolling and shrink-safe rows."""

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Hardware Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(
            "Select the hardware installed on this robot. The selection is saved to hardware.json "
            "and will be used by later build steps to generate firmware feature macros."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        for category in CATEGORY_TITLES:
            devices = DeviceRegistry.by_category(category)
            if not devices:
                continue
            group = QGroupBox(CATEGORY_TITLES[category])
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(10, 8, 10, 8)
            group_layout.setSpacing(8)
            for device in devices:
                item = QWidget(group)
                item_layout = QVBoxLayout(item)
                item_layout.setContentsMargins(0, 0, 0, 0)
                item_layout.setSpacing(2)

                checkbox = QCheckBox(device.display_name)
                checkbox.setObjectName(f"device_{device.device_id}")
                checkbox.setToolTip(device.description)
                self._checkboxes[device.device_id] = checkbox
                item_layout.addWidget(checkbox)

                hint = QLabel(device.description)
                hint.setWordWrap(True)
                hint.setStyleSheet("color: #666666;")
                hint.setContentsMargins(22, 0, 0, 0)
                item_layout.addWidget(hint)
                group_layout.addWidget(item)
            layout.addWidget(group)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        self.save_button = QPushButton("Apply Configuration")
        self.save_button.clicked.connect(self.save)
        button_row.addWidget(self.save_button)
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload)
        button_row.addWidget(self.reload_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(self.status_label.textInteractionFlags())
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        self.scroll_area = make_scroll_area(content)
        root.addWidget(self.scroll_area, 1)
