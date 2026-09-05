"""RoboStudio Robot tab: Discover → Select → OTA → Deploy → Verify."""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QComboBox, QVBoxLayout, QWidget,
)

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


class _DeploymentWorker(QThread):
    completed = Signal(object)

    def __init__(self, code, robot, ssid, wifi_password, ota_password):
        super().__init__()
        self.args = (code, robot, ssid, wifi_password, ota_password)

    def run(self):
        self.completed.emit(RobotDeploymentService().deploy_ota(*self.args))


class RobotTab(QWidget):
    """End-user Golden Path for the current student program."""

    def __init__(self, code_provider, parent=None):
        super().__init__(parent)
        self._code_provider = code_provider
        self._robots: list[RobotInfo] = []
        self._selected: RobotInfo | None = None
        self._discovery_worker = None
        self._deployment_worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Robot Deployment")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        description = QLabel(
            "Find a robot on the local Wi-Fi network, select it, then run "
            "the current student program over OTA."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

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

        self.output_label = QLabel("")
        self.output_label.setWordWrap(True)
        self.output_label.setStyleSheet("font-family: 'Courier New'; color: #666666;")
        layout.addWidget(self.output_label)
        layout.addStretch()

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
        self.output_label.setText("Compiling, building and uploading. Please wait...")

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
        self.output_label.setText(result.output[-2500:] if result.output else "")
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
