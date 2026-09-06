"""RoboStudio USB serial console widget."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QSizePolicy,
    QWidget,
)

from services.serial_console_service import DEFAULT_BAUD_RATE, SerialConsoleError, SerialConsoleService


class SerialConsoleWidget(QWidget):
    """Interactive USB serial monitor/command console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service: SerialConsoleService | None = None
        self._auto_scroll = True
        self._build_ui()
        self._connect_service()
        self.refresh_ports()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        connection_row = QHBoxLayout()
        connection_row.setSpacing(6)
        connection_row.addWidget(QLabel("USB Serial:"))
        self.port_combo = QComboBox()
        self.port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.port_combo.setMinimumWidth(230)
        self.port_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.port_combo.setMinimumContentsLength(24)
        self.port_combo.setMaxVisibleItems(12)
        # Keep the popup wide enough for Windows COM descriptions. The
        # combo itself remains responsive while the popup avoids truncation.
        self.port_combo.view().setMinimumWidth(420)
        connection_row.addWidget(self.port_combo, 1)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_ports)
        connection_row.addWidget(self.refresh_button)
        self.baud_combo = QComboBox()
        self.baud_combo.setMinimumWidth(88)
        self.baud_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for baud in (9600, 19200, 38400, 57600, 115200):
            self.baud_combo.addItem(str(baud), baud)
        self.baud_combo.setCurrentText(str(DEFAULT_BAUD_RATE))
        connection_row.addWidget(self.baud_combo)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        connection_row.addWidget(self.connect_button)
        layout.addLayout(connection_row)

        self.status_label = QLabel("● Disconnected")
        self.status_label.setStyleSheet("font-weight: bold; color: #666666;")
        layout.addWidget(self.status_label)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output.setPlaceholderText("USB serial output will appear here...")
        self.output.setFont(QFont("Courier New", 9))
        self.output.setMinimumHeight(220)
        layout.addWidget(self.output, 1)

        controls_row = QHBoxLayout()
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
        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText("Enter robot command, e.g. help")
        self.command_edit.returnPressed.connect(self.send_command)
        command_row.addWidget(self.command_edit, 1)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_command)
        command_row.addWidget(self.send_button)
        layout.addLayout(command_row)

    def _connect_service(self) -> None:
        try:
            self._service = SerialConsoleService(self)
        except SerialConsoleError as exc:
            self.status_label.setText(f"● Serial unavailable: {exc}")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
            self.connect_button.setEnabled(False)
            self.send_button.setEnabled(False)
            return
        self._service.data_received.connect(self.append_output)
        self._service.connection_changed.connect(self._on_connection_changed)
        self._service.error_occurred.connect(self._on_error)
        self._set_connected_controls(False)

    @property
    def is_connected(self) -> bool:
        return bool(self._service and self._service.is_connected)

    def refresh_ports(self) -> None:
        current = self.port_combo.currentData()
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        for port, description in SerialConsoleService.available_ports():
            self.port_combo.addItem(f"{port} — {description}", port)
        self.port_combo.blockSignals(False)
        if current:
            index = self.port_combo.findData(current)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        if self.port_combo.count() == 0:
            self.port_combo.setPlaceholderText("No USB serial ports found")

    def toggle_connection(self) -> None:
        if self.is_connected:
            self._service.disconnect_port()
            return
        port = self.port_combo.currentData()
        if not port:
            self._on_error("Select a USB serial port first.")
            return
        baud = int(self.baud_combo.currentData())
        self.connect_button.setEnabled(False)
        if not self._service.connect_port(port, baud):
            self.connect_button.setEnabled(True)

    def _on_connection_changed(self, connected: bool, message: str) -> None:
        self.connect_button.setEnabled(True)
        self.connect_button.setText("Disconnect" if connected else "Connect")
        self._set_connected_controls(connected)
        self.status_label.setText(f"● {message}")
        self.status_label.setStyleSheet(
            "font-weight: bold; color: green;" if connected else "font-weight: bold; color: #666666;"
        )
        if not connected:
            self._append_system(f"[SERIAL] {message}")

    def _set_connected_controls(self, connected: bool) -> None:
        self.send_button.setEnabled(connected)
        self.command_edit.setEnabled(connected)
        self.baud_combo.setEnabled(not connected)
        self.port_combo.setEnabled(not connected)

    def _on_error(self, message: str) -> None:
        self.status_label.setText(f"● {message}")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        self._append_system(f"[SERIAL ERROR] {message}")
        self.connect_button.setEnabled(True)

    def append_output(self, text: str) -> None:
        if not text:
            return
        scrollbar = self.output.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 2
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(text)
        if self._auto_scroll or was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(min(scrollbar.value(), scrollbar.maximum()))

    def _append_system(self, text: str) -> None:
        self.append_output(text.rstrip("\n") + "\n")

    def clear(self) -> None:
        self.output.clear()

    def copy(self) -> None:
        self.output.selectAll()
        self.output.copy()
        self.output.moveCursor(QTextCursor.End)

    def _set_auto_scroll(self, enabled: bool) -> None:
        self._auto_scroll = enabled
        if enabled:
            self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())

    def send_command(self) -> None:
        command = self.command_edit.text().strip()
        if not command or not self._service:
            return
        if self._service.send(command):
            self._append_system(f"> {command}")
            self.command_edit.clear()

    def closeEvent(self, event) -> None:
        if self._service:
            self._service.close()
        super().closeEvent(event)
