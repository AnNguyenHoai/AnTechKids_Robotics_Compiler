"""Responsive presentation layer for the existing Robot deployment workflow.

The class intentionally inherits all discovery, first-flash, OTA, registry and
serial behaviour from ``RobotTab``. Phase 1 changes only how those controls are
laid out so resize/DPI pressure cannot force unrelated widgets into each other.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ui.responsive import AdaptiveSplitter, make_scroll_area
from ui.responsive_serial_console import ResponsiveSerialConsoleWidget
from ui.robot_tab import RobotTab


class ResponsiveRobotTab(RobotTab):
    """Robot tab with adaptive wide/stacked workspace and scrolling forms."""

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 12)
        root.setSpacing(10)

        header = QVBoxLayout()
        header.setSpacing(3)
        title = QLabel("Robot Deployment & Console")
        title.setStyleSheet("font-size: 19px; font-weight: 700;")
        header.addWidget(title)
        description = QLabel(
            "First-flash a new robot once, discover robots over Wi-Fi, then deploy student programs over OTA. "
            "Known robots and the selected device are remembered across RoboStudio restarts; offline robots stay visible. "
            "Use the USB Serial Console for direct diagnostics and commands."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666666;")
        header.addWidget(description)
        root.addLayout(header)

        self.responsive_splitter = AdaptiveSplitter()
        deployment_scroll = make_scroll_area(self._build_deployment_panel())
        deployment_scroll.setObjectName("robot_deployment_scroll")
        self.responsive_splitter.addWidget(deployment_scroll)
        self.responsive_splitter.addWidget(self._build_console_panel())
        self.responsive_splitter.setStretchFactor(0, 2)
        self.responsive_splitter.setStretchFactor(1, 3)
        root.addWidget(self.responsive_splitter, 1)

    def _build_deployment_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(9)

        bootstrap_group = QGroupBox("0 · First-Flash Setup")
        bootstrap_form = QFormLayout(bootstrap_group)
        bootstrap_form.setContentsMargins(10, 8, 10, 8)
        bootstrap_form.setVerticalSpacing(7)
        bootstrap_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.bootstrap_ssid_edit = QLineEdit()
        self.bootstrap_ssid_edit.setPlaceholderText("Classroom Wi-Fi network")
        bootstrap_form.addRow("Wi-Fi SSID:", self.bootstrap_ssid_edit)

        self.bootstrap_wifi_password_edit = QLineEdit()
        self.bootstrap_wifi_password_edit.setEchoMode(QLineEdit.Password)
        self.bootstrap_wifi_password_edit.setPlaceholderText("Leave empty if open")
        bootstrap_form.addRow("Wi-Fi Password:", self.bootstrap_wifi_password_edit)

        self.bootstrap_ota_password_edit = QLineEdit()
        self.bootstrap_ota_password_edit.setEchoMode(QLineEdit.Password)
        self.bootstrap_ota_password_edit.setPlaceholderText("OTA password for this robot fleet")
        bootstrap_form.addRow("OTA Password:", self.bootstrap_ota_password_edit)

        usb_container = QWidget()
        usb_layout = QVBoxLayout(usb_container)
        usb_layout.setContentsMargins(0, 0, 0, 0)
        usb_layout.setSpacing(6)

        self.usb_port_combo = QComboBox()
        self.usb_port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.usb_port_combo.setPlaceholderText("No USB/COM port detected")
        self.usb_port_combo.currentIndexChanged.connect(self._refresh_bootstrap_flash_enabled)
        usb_layout.addWidget(self.usb_port_combo)

        # Keep first-flash actions in a 2x2 grid. This remains usable inside the
        # narrow deployment column at high Windows DPI, unlike the old single
        # row that required all three action buttons to fit at once.
        usb_actions = QGridLayout()
        usb_actions.setHorizontalSpacing(6)
        usb_actions.setVerticalSpacing(6)
        self.refresh_usb_button = QPushButton("Refresh USB")
        self.refresh_usb_button.setToolTip("Refresh USB/COM devices visible to Windows.")
        self.refresh_usb_button.clicked.connect(self._refresh_usb_ports)
        usb_actions.addWidget(self.refresh_usb_button, 0, 0)

        self.generate_bootstrap_button = QPushButton("Generate Config")
        self.generate_bootstrap_button.clicked.connect(self.generate_bootstrap)
        usb_actions.addWidget(self.generate_bootstrap_button, 0, 1)

        self.flash_bootstrap_button = QPushButton("Flash via USB")
        self.flash_bootstrap_button.setEnabled(False)
        self.flash_bootstrap_button.clicked.connect(self.flash_bootstrap)
        usb_actions.addWidget(self.flash_bootstrap_button, 1, 0, 1, 2)
        usb_actions.setColumnStretch(0, 1)
        usb_actions.setColumnStretch(1, 1)
        usb_layout.addLayout(usb_actions)
        bootstrap_form.addRow("USB Port:", usb_container)

        self.bootstrap_status = QLabel("No first-flash configuration generated")
        self.bootstrap_status.setWordWrap(True)
        self.bootstrap_status.setMinimumHeight(30)
        bootstrap_form.addRow("Status:", self.bootstrap_status)
        layout.addWidget(bootstrap_group)

        discovery_group = QGroupBox("1 · Select Robot")
        discovery_layout = QVBoxLayout(discovery_group)
        discovery_layout.setContentsMargins(10, 8, 10, 8)
        discovery_layout.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.robot_combo = QComboBox()
        self.robot_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.robot_combo.setPlaceholderText("Select a known robot")
        self.robot_combo.currentIndexChanged.connect(self._on_robot_selected)
        row.addWidget(self.robot_combo, 1)
        self.refresh_button = QPushButton("Discover")
        self.refresh_button.setToolTip("Refresh online/offline state for all known robots on the local network.")
        self.refresh_button.clicked.connect(self.discover)
        row.addWidget(self.refresh_button)
        discovery_layout.addLayout(row)

        self.robot_status = QLabel("No robot selected")
        self.robot_status.setWordWrap(True)
        self.robot_status.setStyleSheet("font-weight: 600;")
        discovery_layout.addWidget(self.robot_status)

        self.robot_details = QLabel("")
        self.robot_details.setWordWrap(True)
        self.robot_details.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.robot_details.setStyleSheet("color: #666666;")
        discovery_layout.addWidget(self.robot_details)
        layout.addWidget(discovery_group)

        connection_group = QGroupBox("2 · Wi-Fi / OTA")
        form = QFormLayout(connection_group)
        form.setContentsMargins(10, 8, 10, 8)
        form.setVerticalSpacing(7)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.ssid_edit = QLineEdit()
        self.ssid_edit.setPlaceholderText("Wi-Fi network used by the robot")
        form.addRow("Wi-Fi SSID:", self.ssid_edit)

        self.wifi_password_edit = QLineEdit()
        self.wifi_password_edit.setEchoMode(QLineEdit.Password)
        self.wifi_password_edit.setPlaceholderText("Optional if Wi-Fi is open")
        form.addRow("Wi-Fi Password:", self.wifi_password_edit)

        self.ota_password_edit = QLineEdit()
        self.ota_password_edit.setEchoMode(QLineEdit.Password)
        self.ota_password_edit.setPlaceholderText("Required for OTA")
        form.addRow("OTA Password:", self.ota_password_edit)
        layout.addWidget(connection_group)

        run_group = QGroupBox("3 · Run on Robot")
        run_layout = QVBoxLayout(run_group)
        run_layout.setContentsMargins(10, 8, 10, 8)
        run_layout.setSpacing(6)
        self.deploy_button = QPushButton("▶  RUN ON ROBOT")
        self.deploy_button.setMinimumHeight(44)
        self.deploy_button.setToolTip("Compile and deploy the current program to the selected online robot.")
        self.deploy_button.setEnabled(False)
        self.deploy_button.clicked.connect(self.deploy)
        run_layout.addWidget(self.deploy_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        run_layout.addWidget(self.progress)

        self.result_label = QLabel("Ready — select an online robot and compile a program to enable Run.")
        self.result_label.setWordWrap(True)
        run_layout.addWidget(self.result_label)
        layout.addWidget(run_group)
        layout.addStretch(1)
        return panel

    def _build_console_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(0)

        diagnostics_splitter = QSplitter(Qt.Vertical)
        diagnostics_splitter.setChildrenCollapsible(False)
        diagnostics_splitter.setHandleWidth(6)

        serial_group = QGroupBox("USB Serial Console")
        serial_layout = QVBoxLayout(serial_group)
        serial_layout.setContentsMargins(10, 8, 10, 8)
        self.serial_console = ResponsiveSerialConsoleWidget(serial_group)
        serial_layout.addWidget(self.serial_console)
        diagnostics_splitter.addWidget(serial_group)

        log_group = QGroupBox("Deployment Logs")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 8, 10, 8)
        log_layout.setSpacing(6)

        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("PlatformIO output"))
        log_header.addStretch()
        self.clear_logs_button = QPushButton("Clear")
        self.clear_logs_button.setToolTip("Clear the deployment log view.")
        self.clear_logs_button.clicked.connect(self.clear_logs)
        log_header.addWidget(self.clear_logs_button)
        self.copy_logs_button = QPushButton("Copy")
        self.copy_logs_button.setToolTip("Copy the complete deployment log to the clipboard.")
        self.copy_logs_button.clicked.connect(self.copy_logs)
        log_header.addWidget(self.copy_logs_button)
        log_layout.addLayout(log_header)

        self.output_label = QPlainTextEdit()
        self.output_label.setReadOnly(True)
        self.output_label.setPlaceholderText("Deployment and PlatformIO logs will appear here...")
        self.output_label.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output_label.setFont(self._console_font())
        self.output_label.setMinimumHeight(110)
        self.output_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        log_layout.addWidget(self.output_label, 1)
        diagnostics_splitter.addWidget(log_group)

        diagnostics_splitter.setStretchFactor(0, 3)
        diagnostics_splitter.setStretchFactor(1, 2)
        diagnostics_splitter.setSizes([360, 240])
        layout.addWidget(diagnostics_splitter, 1)
        return panel
