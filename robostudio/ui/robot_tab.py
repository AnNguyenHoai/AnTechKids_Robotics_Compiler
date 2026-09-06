"""RoboStudio Robot tab: first-flash bootstrap + Discover → Select → OTA → Deploy → Verify."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QComboBox, QVBoxLayout, QWidget,
)

from services.bootstrap_config_service import BootstrapConfigService
from services.robot_deployment_service import RobotDeploymentService, RobotInfo
from services.robot_discovery_service import RobotDiscoveryClient


class _DiscoveryWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def run(self):
        try:
            self.completed.emit(RobotDiscoveryClient().discover())
        except Exception as exc:
            self.failed.emit(str(exc))


class _BootstrapFlashWorker(QThread):
    completed = Signal(object)

    def __init__(self, config_path, usb_port):
        super().__init__()
        self.config_path = config_path
        self.usb_port = usb_port

    def run(self):
        result = RobotDeploymentService().flash_first_robot(
            Path(self.config_path), self.usb_port
        )
        self.completed.emit(result)


class _DeploymentWorker(QThread):
    completed = Signal(object)

    def __init__(self, code, robot, ssid, wifi_password, ota_password):
        super().__init__()
        self.args = (code, robot, ssid, wifi_password, ota_password)

    def run(self):
        self.completed.emit(RobotDeploymentService().deploy_ota(*self.args))


class RobotTab(QWidget):
    """End-user Golden Path plus teacher-only first-flash bootstrap setup."""

    def __init__(self, code_provider, parent=None):
        super().__init__(parent)
        self._code_provider = code_provider
        self._robots: list[RobotInfo] = []
        self._selected: RobotInfo | None = None
        self._bootstrap_path: Path | None = None
        self._discovery_worker = None
        self._bootstrap_flash_worker = None
        self._deployment_worker = None
        self._bootstrap_service = BootstrapConfigService()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Robot Deployment")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        description = QLabel(
            "Set up a new robot once, then discover and run student programs over OTA. "
            "First-flash Wi-Fi data is generated locally and provisioned through PlatformIO."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        bootstrap_group = QGroupBox("0. First-Flash Setup (Teacher)")
        bootstrap_form = QFormLayout(bootstrap_group)
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

        usb_row = QHBoxLayout()
        self.usb_port_edit = QLineEdit()
        self.usb_port_edit.setPlaceholderText("Optional, e.g. COM4")
        usb_row.addWidget(self.usb_port_edit, 1)
        self.generate_bootstrap_button = QPushButton("Generate First-Flash Config")
        self.generate_bootstrap_button.clicked.connect(self.generate_bootstrap)
        usb_row.addWidget(self.generate_bootstrap_button)
        self.flash_bootstrap_button = QPushButton("Flash New Robot via USB (PlatformIO)")
        self.flash_bootstrap_button.setEnabled(False)
        self.flash_bootstrap_button.clicked.connect(self.flash_bootstrap)
        usb_row.addWidget(self.flash_bootstrap_button)
        bootstrap_form.addRow("USB Port:", usb_row)
        self.bootstrap_status = QLabel("No first-flash configuration generated")
        self.bootstrap_status.setWordWrap(True)
        bootstrap_form.addRow("Status:", self.bootstrap_status)
        layout.addWidget(bootstrap_group)

        discovery_group = QGroupBox("1. Select Robot")
        discovery_layout = QVBoxLayout(discovery_group)
        row = QHBoxLayout()
        self.robot_combo = QComboBox()
        self.robot_combo.setMinimumWidth(360)
        self.robot_combo.currentIndexChanged.connect(self._on_robot_selected)
        row.addWidget(self.robot_combo, 1)
        self.refresh_button = QPushButton("Discover Robots")
        self.refresh_button.clicked.connect(self.discover)
        row.addWidget(self.refresh_button)
        discovery_layout.addLayout(row)
        self.robot_status = QLabel("No robot selected")
        self.robot_status.setWordWrap(True)
        discovery_layout.addWidget(self.robot_status)
        self.robot_details = QLabel("")
        self.robot_details.setWordWrap(True)
        self.robot_details.setStyleSheet("color: #666666;")
        discovery_layout.addWidget(self.robot_details)
        layout.addWidget(discovery_group)

        connection_group = QGroupBox("2. Wi-Fi / OTA")
        form = QFormLayout(connection_group)
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

        run_group = QGroupBox("3. Run")
        run_layout = QVBoxLayout(run_group)
        self.deploy_button = QPushButton("▶  RUN ON ROBOT")
        self.deploy_button.setMinimumHeight(42)
        self.deploy_button.setEnabled(False)
        self.deploy_button.clicked.connect(self.deploy)
        run_layout.addWidget(self.deploy_button)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        run_layout.addWidget(self.progress)
        self.result_label = QLabel("Ready")
        self.result_label.setWordWrap(True)
        run_layout.addWidget(self.result_label)
        layout.addWidget(run_group)

        log_header = QHBoxLayout()
        log_title = QLabel("Deployment Logs")
        log_title.setStyleSheet("font-weight: bold;")
        log_header.addWidget(log_title)
        log_header.addStretch()
        self.clear_logs_button = QPushButton("Clear Logs")
        self.clear_logs_button.clicked.connect(self.clear_logs)
        log_header.addWidget(self.clear_logs_button)
        self.copy_logs_button = QPushButton("Copy Log")
        self.copy_logs_button.clicked.connect(self.copy_logs)
        log_header.addWidget(self.copy_logs_button)
        layout.addLayout(log_header)

        self.output_label = QPlainTextEdit()
        self.output_label.setReadOnly(True)
        self.output_label.setPlaceholderText("Deployment and PlatformIO logs will appear here...")
        self.output_label.setMinimumHeight(180)
        self.output_label.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output_label.setStyleSheet("font-family: 'Courier New';")
        layout.addWidget(self.output_label, 1)

    def set_logs(self, text: str):
        """Replace the visible deployment log without truncating its contents."""
        self.output_label.setPlainText(text or "")
        self.output_label.verticalScrollBar().setValue(
            self.output_label.verticalScrollBar().maximum()
        )

    def clear_logs(self):
        """Remove all deployment logs currently displayed in the UI."""
        self.output_label.clear()

    def copy_logs(self):
        """Copy the complete deployment log to the system clipboard."""
        self.output_label.selectAll()
        self.output_label.copy()
        self.output_label.moveCursor(self.output_label.textCursor().MoveOperation.End)

    def generate_bootstrap(self):
        ssid = self.bootstrap_ssid_edit.text().strip()
        wifi_password = self.bootstrap_wifi_password_edit.text()
        ota_password = self.bootstrap_ota_password_edit.text()
        try:
            path = self._bootstrap_service.generate(ssid, wifi_password, ota_password)
        except (ValueError, RuntimeError, OSError) as exc:
            QMessageBox.warning(self, "Bootstrap configuration", str(exc))
            return
        self._bootstrap_path = path
        self.flash_bootstrap_button.setEnabled(True)
        self.bootstrap_status.setText(
            "✓ First-flash configuration ready.\n"
            f"Bootstrap artifact: {path}\n"
            "Click 'Flash New Robot via USB (PlatformIO)' to build and upload the "
            "bootstrap firmware directly."
        )
        self.bootstrap_status.setStyleSheet("font-weight: bold; color: green;")

    def flash_bootstrap(self):
        if self._bootstrap_path is None:
            return
        if self._bootstrap_flash_worker and self._bootstrap_flash_worker.isRunning():
            return

        self.generate_bootstrap_button.setEnabled(False)
        self.flash_bootstrap_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.progress.setVisible(True)
        self.result_label.setText("Building and flashing first-boot firmware with PlatformIO...")
        self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
        self.bootstrap_status.setText(
            "PlatformIO is building the bootstrap firmware and uploading it over USB. "
            "Keep the robot connected until the upload completes."
        )
        self.set_logs("PlatformIO first-flash in progress...")

        self._bootstrap_flash_worker = _BootstrapFlashWorker(
            self._bootstrap_path, self.usb_port_edit.text().strip()
        )
        self._bootstrap_flash_worker.completed.connect(self._on_bootstrap_flash_finished)
        self._bootstrap_flash_worker.finished.connect(self._bootstrap_flash_finished)
        self._bootstrap_flash_worker.start()

    def _bootstrap_flash_finished(self):
        self.progress.setVisible(False)
        self.generate_bootstrap_button.setEnabled(True)
        self.refresh_button.setEnabled(True)

    def _on_bootstrap_flash_finished(self, result):
        self.set_logs(result.output or "")
        if result.success:
            if result.verified_robot:
                self.bootstrap_status.setText(
                    "✓ First flash complete and robot discovered.\n"
                    f"Robot: {result.verified_robot.display_label} @ {result.verified_robot.ip}"
                )
            else:
                self.bootstrap_status.setText(
                    "✓ First flash completed. Robot discovery timed out; "
                    "wait for Wi-Fi and click Discover Robots."
                )
            self.bootstrap_status.setStyleSheet("font-weight: bold; color: green;")
            self.result_label.setText("✓ First-flash upload completed.")
            self.result_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.bootstrap_status.setText(
                f"✗ First-flash failed: {result.error or 'unknown error'}"
            )
            self.bootstrap_status.setStyleSheet("font-weight: bold; color: red;")
            self.result_label.setText("First-flash failed. Check the PlatformIO output.")
            self.result_label.setStyleSheet("font-weight: bold; color: red;")

    def discover(self):
        if self._discovery_worker and self._discovery_worker.isRunning():
            return
        self.refresh_button.setEnabled(False)
        self.robot_combo.clear()
        self._robots = []
        self._selected = None
        self.robot_status.setText("Searching for robots...")
        self.robot_details.setText("")
        self.result_label.setText("Discovery in progress...")
        self._refresh_deploy_enabled()
        self._discovery_worker = _DiscoveryWorker()
        self._discovery_worker.completed.connect(self._on_discovered)
        self._discovery_worker.failed.connect(self._on_discovery_failed)
        self._discovery_worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self._discovery_worker.start()

    def _on_discovered(self, robots):
        self._robots = list(robots)
        self.robot_combo.blockSignals(True)
        self.robot_combo.clear()
        for robot in self._robots:
            state = "Ready" if robot.ready else "Not ready"
            self.robot_combo.addItem(f"{robot.display_label} — {state}", robot.device_id)
        self.robot_combo.blockSignals(False)
        if self._robots:
            self.robot_combo.setCurrentIndex(0)
            self._on_robot_selected(0)
            self.robot_status.setText(f"Found {len(self._robots)} robot(s).")
        else:
            self.robot_status.setText(
                "No robot found. Make sure the robot is powered on and "
                "connected to the same Wi-Fi network."
            )
            self._refresh_deploy_enabled()

    def _on_discovery_failed(self, message):
        self._selected = None
        self.robot_combo.clear()
        self.robot_status.setText(f"Discovery failed: {message}")
        self.result_label.setText("Discovery failed. Check the Wi-Fi network and try again.")
        self._refresh_deploy_enabled()

    def _on_robot_selected(self, index):
        self._selected = self._robots[index] if 0 <= index < len(self._robots) else None
        if self._selected is None:
            self.robot_status.setText("No robot selected")
            self.robot_details.setText("")
            self._refresh_deploy_enabled()
            return
        robot = self._selected
        capabilities = ", ".join(
            name.replace("_", " ") for name, enabled in robot.capabilities.items() if enabled
        ) or "None"
        self.robot_status.setText(
            f"● {'Ready' if robot.ready else 'Not ready'} | {robot.hostname} | {robot.ip}"
        )
        self.robot_details.setText(
            f"Device ID: {robot.device_id}\n"
            f"Target: {robot.target}   Firmware: {robot.firmware}\n"
            f"OTA: {'Available' if robot.ota else 'Unavailable'}\n"
            f"Capabilities: {capabilities}"
        )
        self._refresh_deploy_enabled()

    def _refresh_deploy_enabled(self):
        code_available = bool(self._code_provider().strip())
        self.deploy_button.setEnabled(
            self._selected is not None and self._selected.ready and
            self._selected.ota and code_available and
            not (self._deployment_worker and self._deployment_worker.isRunning())
        )

    def deploy(self):
        robot = self._selected
        code = self._code_provider()
        if robot is None or not code.strip():
            return
        ssid = self.ssid_edit.text().strip()
        wifi_password = self.wifi_password_edit.text()
        ota_password = self.ota_password_edit.text()
        if not ssid or not ota_password:
            QMessageBox.warning(
                self, "OTA settings required",
                "Enter the robot Wi-Fi SSID and OTA password before deploying.",
            )
            return

        self.deploy_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.progress.setVisible(True)
        self.result_label.setText(f"Deploying to {robot.display_label}...")
        self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
        self.set_logs("Compiling, building and uploading. Please wait...")

        self._deployment_worker = _DeploymentWorker(
            code, robot, ssid, wifi_password, ota_password
        )
        self._deployment_worker.completed.connect(self._on_deploy_finished)
        self._deployment_worker.finished.connect(self._deployment_finished)
        self._deployment_worker.start()

    def _deployment_finished(self):
        self.progress.setVisible(False)
        self.refresh_button.setEnabled(True)

    def _on_deploy_finished(self, result):
        self.set_logs(result.output or "")
        if result.success:
            verified = result.verified_robot
            self.result_label.setText(
                f"✓ Deployment verified — {verified.display_label} is ready and running."
            )
            self.result_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.result_label.setText(f"✗ {result.error or 'Deployment failed.'}")
            self.result_label.setStyleSheet("font-weight: bold; color: red;")
        self._refresh_deploy_enabled()

    def refresh_code_state(self):
        """Re-evaluate whether the current editor has code ready to deploy."""
        self._refresh_deploy_enabled()
