"""Production-oriented responsive presentation for the Robot workflow.

Phase 2 keeps discovery, first-flash, OTA, registry and serial behaviour in the
existing ``RobotTab``. This module changes information hierarchy only: everyday
Run actions stay visible, one-time setup moves to a guided flow, and diagnostics
are available on demand without competing for screen space.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui import theme
from ui.components import DisclosureButton, StatusBadge, SummaryCard
from ui.first_flash_dialog import FirstFlashSetupDialog
from ui.responsive import AdaptiveSplitter, make_scroll_area
from ui.responsive_serial_console import ResponsiveSerialConsoleWidget
from ui.robot_tab import RobotTab


class ResponsiveRobotTab(RobotTab):
    """Robot tab focused on the daily select-and-run golden path."""

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 12)
        root.setSpacing(10)

        header = QVBoxLayout()
        header.setSpacing(3)
        title = QLabel("Robot")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {theme.TEXT_PRIMARY};")
        header.addWidget(title)
        description = QLabel(
            "Select a robot and run the current program. New-robot setup and diagnostics are available when needed."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        header.addWidget(description)
        root.addLayout(header)

        self._build_first_flash_flow()

        self.responsive_splitter = AdaptiveSplitter()
        deployment_scroll = make_scroll_area(self._build_deployment_panel())
        deployment_scroll.setObjectName("robot_deployment_scroll")
        self.responsive_splitter.addWidget(deployment_scroll)
        self.responsive_splitter.addWidget(self._build_console_panel())
        self.responsive_splitter.setStretchFactor(0, 2)
        self.responsive_splitter.setStretchFactor(1, 3)
        root.addWidget(self.responsive_splitter, 1)

    def _build_first_flash_flow(self) -> None:
        self.first_flash_dialog = FirstFlashSetupDialog(
            self,
            on_refresh_usb=self._refresh_usb_ports,
            on_flash=self._start_first_flash,
        )
        # Preserve the inherited RobotTab field contract. The guided dialog owns
        # the widgets, while the existing deployment methods continue to use the
        # same attribute names and service boundaries.
        self.bootstrap_ssid_edit = self.first_flash_dialog.ssid_edit
        self.bootstrap_wifi_password_edit = self.first_flash_dialog.wifi_password_edit
        self.bootstrap_ota_password_edit = self.first_flash_dialog.ota_password_edit
        self.usb_port_combo = self.first_flash_dialog.usb_port_combo
        self.refresh_usb_button = self.first_flash_dialog.refresh_usb_button
        self.generate_bootstrap_button = self.first_flash_dialog.generate_compat_button
        self.flash_bootstrap_button = self.first_flash_dialog.flash_button
        self.bootstrap_status = self.first_flash_dialog.status_label
        self.usb_port_combo.currentIndexChanged.connect(self._refresh_bootstrap_flash_enabled)

    def _build_deployment_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(10)

        robot_card = SummaryCard("My Robot")
        robot_row = QHBoxLayout()
        robot_row.setSpacing(6)
        self.robot_combo = QComboBox()
        self.robot_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.robot_combo.setPlaceholderText("Select a known robot")
        self.robot_combo.currentIndexChanged.connect(self._on_robot_selected)
        robot_row.addWidget(self.robot_combo, 1)
        self.refresh_button = QPushButton("Discover")
        self.refresh_button.setToolTip("Refresh online/offline state for known robots on the local network.")
        self.refresh_button.setStyleSheet(theme.secondary_button_style())
        self.refresh_button.clicked.connect(self.discover)
        robot_row.addWidget(self.refresh_button)
        robot_card.layout.addLayout(robot_row)

        state_row = QHBoxLayout()
        self.robot_badge = StatusBadge("No robot selected", "neutral")
        state_row.addWidget(self.robot_badge)
        state_row.addStretch(1)
        self.robot_details_toggle = DisclosureButton("Robot details")
        state_row.addWidget(self.robot_details_toggle)
        robot_card.layout.addLayout(state_row)

        self.robot_status = QLabel("No robot selected")
        self.robot_status.setWordWrap(True)
        self.robot_status.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; border: none;")
        robot_card.add_widget(self.robot_status)

        self.robot_details = QLabel("")
        self.robot_details.setWordWrap(True)
        self.robot_details.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.robot_details.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; border: none;")
        self.robot_details.setVisible(False)
        self.robot_details_toggle.toggled.connect(self.robot_details.setVisible)
        robot_card.add_widget(self.robot_details)
        layout.addWidget(robot_card)

        connection_group = QGroupBox("Deployment Connection")
        form = QFormLayout(connection_group)
        form.setContentsMargins(10, 8, 10, 8)
        form.setVerticalSpacing(7)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        connection_hint = QLabel("Used when sending the current program to the selected robot over Wi-Fi.")
        connection_hint.setWordWrap(True)
        connection_hint.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        form.addRow(connection_hint)

        self.ssid_edit = QLineEdit()
        self.ssid_edit.setPlaceholderText("Wi-Fi network used by the robot")
        form.addRow("Wi-Fi SSID:", self.ssid_edit)

        self.wifi_password_edit = QLineEdit()
        self.wifi_password_edit.setEchoMode(QLineEdit.Password)
        self.wifi_password_edit.setPlaceholderText("Optional if Wi-Fi is open")
        form.addRow("Wi-Fi Password:", self.wifi_password_edit)

        self.ota_password_edit = QLineEdit()
        self.ota_password_edit.setEchoMode(QLineEdit.Password)
        self.ota_password_edit.setPlaceholderText("Robot password")
        form.addRow("Robot Password:", self.ota_password_edit)
        layout.addWidget(connection_group)

        run_card = SummaryCard("Run Current Program")
        readiness_row = QHBoxLayout()
        self.program_badge = StatusBadge("No program", "neutral")
        readiness_row.addWidget(self.program_badge)
        readiness_row.addStretch(1)
        run_card.layout.addLayout(readiness_row)

        self.deploy_button = QPushButton("▶  RUN ON ROBOT")
        self.deploy_button.setMinimumHeight(46)
        self.deploy_button.setStyleSheet(theme.primary_button_style())
        self.deploy_button.setToolTip("Compile and deploy the current program to the selected online robot.")
        self.deploy_button.setEnabled(False)
        self.deploy_button.clicked.connect(self.deploy)
        run_card.add_widget(self.deploy_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        run_card.add_widget(self.progress)

        self.result_label = QLabel("Select an online robot and load a program to enable Run.")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; border: none;")
        run_card.add_widget(self.result_label)
        layout.addWidget(run_card)

        setup_card = SummaryCard("New Robot")
        setup_hint = QLabel("First time only: connect a new robot by USB and configure its network.")
        setup_hint.setWordWrap(True)
        setup_hint.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; border: none;")
        setup_card.add_widget(setup_hint)
        self.setup_robot_button = QPushButton("＋ Setup New Robot")
        self.setup_robot_button.setStyleSheet(theme.secondary_button_style())
        self.setup_robot_button.clicked.connect(self.first_flash_dialog.show_start)
        setup_card.add_widget(self.setup_robot_button)
        layout.addWidget(setup_card)

        layout.addStretch(1)
        return panel

    def _build_console_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(6)

        heading = QLabel("Diagnostics")
        heading.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {theme.TEXT_PRIMARY};")
        layout.addWidget(heading)
        hint = QLabel("Open these tools only when you need direct serial output or deployment details.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        layout.addWidget(hint)

        self.diagnostics_tabs = QTabWidget()
        self.diagnostics_tabs.setDocumentMode(True)

        serial_tab = QWidget()
        serial_layout = QVBoxLayout(serial_tab)
        serial_layout.setContentsMargins(8, 8, 8, 8)
        self.serial_console = ResponsiveSerialConsoleWidget(serial_tab)
        serial_layout.addWidget(self.serial_console)
        self.diagnostics_tabs.addTab(serial_tab, "Serial Console")

        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(8, 8, 8, 8)
        log_layout.setSpacing(6)
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("PlatformIO output"))
        log_header.addStretch(1)
        self.clear_logs_button = QPushButton("Clear")
        self.clear_logs_button.clicked.connect(self.clear_logs)
        log_header.addWidget(self.clear_logs_button)
        self.copy_logs_button = QPushButton("Copy")
        self.copy_logs_button.clicked.connect(self.copy_logs)
        log_header.addWidget(self.copy_logs_button)
        log_layout.addLayout(log_header)

        self.output_label = QPlainTextEdit()
        self.output_label.setReadOnly(True)
        self.output_label.setPlaceholderText("Deployment and PlatformIO logs will appear here...")
        self.output_label.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output_label.setFont(self._console_font())
        self.output_label.setMinimumHeight(140)
        self.output_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        log_layout.addWidget(self.output_label, 1)
        self.diagnostics_tabs.addTab(log_tab, "Deployment Log")

        layout.addWidget(self.diagnostics_tabs, 1)
        return panel

    def _start_first_flash(self) -> None:
        """Prepare bootstrap config implicitly, then use the existing flash path."""
        if not self._selected_usb_port():
            self.bootstrap_status.setText("Select a USB/COM port before flashing the robot.")
            self.bootstrap_status.setStyleSheet(f"font-weight: 600; color: {theme.WARNING};")
            return
        # Never reuse a stale config if the user changed or invalidated the
        # network fields in the guided flow.
        self._bootstrap_path = None
        self.generate_bootstrap()
        if self._bootstrap_path is None:
            return
        super().flash_bootstrap()

    def _refresh_bootstrap_flash_enabled(self):
        """Phase 2 enables Flash once a port exists; config is generated implicitly."""
        running = bool(self._bootstrap_flash_worker and self._bootstrap_flash_worker.isRunning())
        self.flash_bootstrap_button.setEnabled(bool(self._selected_usb_port()) and not running)

    def _render_selected_details(self) -> None:
        super()._render_selected_details()
        if self._selected is None:
            self.robot_badge.set_status("No robot selected", "neutral")
            return
        item = self._selected
        robot = item.robot
        if item.online and robot.ready:
            self.robot_badge.set_status("● Online · Ready", "success")
        elif item.online:
            self.robot_badge.set_status("● Online · Needs attention", "warning")
        else:
            self.robot_badge.set_status("○ Offline", "neutral")

    def _refresh_deploy_enabled(self):
        super()._refresh_deploy_enabled()
        if not hasattr(self, "program_badge"):
            return
        code_available = bool(self._code_provider().strip())
        if code_available:
            self.program_badge.set_status("✓ Program loaded", "success")
        else:
            self.program_badge.set_status("No program", "neutral")

    def discover(self):
        if hasattr(self, "robot_badge"):
            self.robot_badge.set_status("Searching…", "warning")
        super().discover()
