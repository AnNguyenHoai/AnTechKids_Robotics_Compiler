"""Guided first-flash setup flow for a new robot."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui import theme


class FirstFlashSetupDialog(QDialog):
    """Two-step setup that hides bootstrap implementation details from users."""

    def __init__(
        self,
        parent=None,
        *,
        on_refresh_usb: Callable[[], None] | None = None,
        on_flash: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self._on_refresh_usb = on_refresh_usb
        self._on_flash = on_flash
        self.setWindowTitle("Setup New Robot")
        self.setModal(False)
        self.resize(560, 430)
        self.setMinimumSize(480, 380)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        title = QLabel("Setup New Robot")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {theme.TEXT_PRIMARY};")
        root.addWidget(title)

        self.step_label = QLabel("Step 1 of 2 · Network")
        self.step_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        root.addWidget(self.step_label)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_network_step())
        self.stack.addWidget(self._build_usb_step())
        root.addWidget(self.stack, 1)

        nav = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setEnabled(False)
        self.back_button.clicked.connect(self._back)
        nav.addWidget(self.back_button)
        nav.addStretch(1)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        nav.addWidget(self.close_button)
        self.next_button = QPushButton("Continue")
        self.next_button.setStyleSheet(theme.primary_button_style())
        self.next_button.clicked.connect(self._next)
        nav.addWidget(self.next_button)
        root.addLayout(nav)

    def _build_network_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        description = QLabel(
            "Enter the Wi-Fi settings the robot should use after its first USB flash. "
            "RoboStudio will prepare the bootstrap configuration automatically."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        layout.addWidget(description)

        form = QFormLayout()
        form.setVerticalSpacing(9)
        self.ssid_edit = QLineEdit()
        self.ssid_edit.setPlaceholderText("Classroom Wi-Fi network")
        form.addRow("Wi-Fi SSID:", self.ssid_edit)

        self.wifi_password_edit = QLineEdit()
        self.wifi_password_edit.setEchoMode(QLineEdit.Password)
        self.wifi_password_edit.setPlaceholderText("Leave empty if the network is open")
        form.addRow("Wi-Fi Password:", self.wifi_password_edit)

        self.ota_password_edit = QLineEdit()
        self.ota_password_edit.setEchoMode(QLineEdit.Password)
        self.ota_password_edit.setPlaceholderText("Password used for future wireless deployments")
        form.addRow("Robot Password:", self.ota_password_edit)
        layout.addLayout(form)
        layout.addStretch(1)
        return page

    def _build_usb_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        description = QLabel(
            "Connect the robot by USB, select its COM port, then flash it once. "
            "Keep the cable connected until RoboStudio reports completion."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        layout.addWidget(description)

        self.usb_port_combo = QComboBox()
        self.usb_port_combo.setPlaceholderText("No USB/COM port detected")
        layout.addWidget(self.usb_port_combo)

        actions = QHBoxLayout()
        self.refresh_usb_button = QPushButton("Refresh USB")
        if self._on_refresh_usb:
            self.refresh_usb_button.clicked.connect(self._on_refresh_usb)
        actions.addWidget(self.refresh_usb_button)

        # Compatibility-only control: inherited deployment logic toggles this
        # widget while a flash is running, but Phase 2 no longer exposes a
        # separate "Generate Config" action to the user.
        self.generate_compat_button = QPushButton("Prepare")
        self.generate_compat_button.setVisible(False)

        self.flash_button = QPushButton("Flash Robot")
        self.flash_button.setEnabled(False)
        self.flash_button.setStyleSheet(theme.primary_button_style())
        if self._on_flash:
            self.flash_button.clicked.connect(self._on_flash)
        actions.addWidget(self.flash_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.status_label = QLabel("Connect a robot and choose its USB/COM port.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        return page

    def _next(self) -> None:
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)
            self.step_label.setText("Step 2 of 2 · USB Flash")
            self.back_button.setEnabled(True)
            self.next_button.setVisible(False)
            if self._on_refresh_usb:
                self._on_refresh_usb()

    def _back(self) -> None:
        self.stack.setCurrentIndex(0)
        self.step_label.setText("Step 1 of 2 · Network")
        self.back_button.setEnabled(False)
        self.next_button.setVisible(True)

    def show_start(self) -> None:
        self.stack.setCurrentIndex(0)
        self.step_label.setText("Step 1 of 2 · Network")
        self.back_button.setEnabled(False)
        self.next_button.setVisible(True)
        self.show()
        self.raise_()
        self.activateWindow()
