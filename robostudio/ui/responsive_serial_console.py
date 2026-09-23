"""Responsive presentation for the existing USB serial console behaviour."""
from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from services.serial_console_service import DEFAULT_BAUD_RATE
from ui.serial_console import SerialConsoleWidget


class ResponsiveSerialConsoleWidget(SerialConsoleWidget):
    """Serial console with a two-row connection toolbar that can shrink safely.

    All connection/send behaviour stays inherited from ``SerialConsoleWidget``;
    only widget geometry is replaced.
    """

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        connection_grid = QGridLayout()
        connection_grid.setHorizontalSpacing(6)
        connection_grid.setVerticalSpacing(6)

        connection_grid.addWidget(QLabel("USB Serial:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.port_combo.setMinimumWidth(120)
        self.port_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.port_combo.setMinimumContentsLength(12)
        self.port_combo.setMaxVisibleItems(12)
        # Popup width may exceed the control width without forcing the layout
        # itself to stay wide.
        self.port_combo.view().setMinimumWidth(420)
        connection_grid.addWidget(self.port_combo, 0, 1, 1, 4)

        connection_grid.addWidget(QLabel("Baud:"), 1, 0)
        self.baud_combo = QComboBox()
        self.baud_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for baud in (9600, 19200, 38400, 57600, 115200):
            self.baud_combo.addItem(str(baud), baud)
        self.baud_combo.setCurrentText(str(DEFAULT_BAUD_RATE))
        connection_grid.addWidget(self.baud_combo, 1, 1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_ports)
        connection_grid.addWidget(self.refresh_button, 1, 2)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        connection_grid.addWidget(self.connect_button, 1, 3)
        connection_grid.setColumnStretch(4, 1)
        layout.addLayout(connection_grid)

        self.status_label = QLabel("● Disconnected")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-weight: bold; color: #666666;")
        layout.addWidget(self.status_label)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output.setPlaceholderText("USB serial output will appear here...")
        self.output.setFont(QFont("Courier New", 9))
        self.output.setMinimumHeight(110)
        self.output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.output, 1)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)
        controls_row.addWidget(self.clear_button)
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy)
        controls_row.addWidget(self.copy_button)
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.toggled.connect(self._set_auto_scroll)
        controls_row.addWidget(self.auto_scroll_check)
        controls_row.addStretch()
        layout.addLayout(controls_row)

        command_row = QHBoxLayout()
        command_row.setSpacing(6)
        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText("Enter robot command, e.g. help")
        self.command_edit.returnPressed.connect(self.send_command)
        command_row.addWidget(self.command_edit, 1)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_command)
        command_row.addWidget(self.send_button)
        layout.addLayout(command_row)
