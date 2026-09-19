"""RoboStudio Robot tab: stable deployment workflow and multi-robot management."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QComboBox, QSizePolicy,
    QSplitter, QVBoxLayout, QWidget,
)

from services.bootstrap_config_service import BootstrapConfigService
from services.robot_deployment_service import RobotDeploymentService, DeploymentResult
from services.robot_discovery_service import RobotDiscoveryClient, RobotInfo
from services.robot_registry_service import ManagedRobot, RobotRegistryError, RobotRegistryService
from services.serial_console_service import SerialConsoleService
from ui.serial_console import SerialConsoleWidget


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
    output = Signal(str)

    def __init__(self, config_path, usb_port):
        super().__init__()
        self.config_path = config_path
        self.usb_port = usb_port

    def run(self):
        try:
            result = RobotDeploymentService().flash_first_robot(
                Path(self.config_path), self.usb_port, self.output.emit
            )
        except Exception as exc:
            result = DeploymentResult(False, "", f"First-flash runtime error: {exc}")
        self.completed.emit(result)


class _DeploymentWorker(QThread):
    completed = Signal(object)
    output = Signal(str)

    def __init__(self, code, robot, ssid, wifi_password, ota_password):
        super().__init__()
        self.args = (code, robot, ssid, wifi_password, ota_password)

    def run(self):
        try:
            result = RobotDeploymentService().deploy_ota(*self.args, on_output=self.output.emit)
        except Exception as exc:
            result = DeploymentResult(False, "", f"Deployment runtime error: {exc}")
        self.completed.emit(result)


class RobotTab(QWidget):
    """End-user Golden Path plus persistent multi-robot fleet selection."""

    def __init__(self, code_provider, parent=None):
        super().__init__(parent)
        self._code_provider = code_provider
        self._robots: list[ManagedRobot] = []
        self._selected: ManagedRobot | None = None
        self._bootstrap_path: Path | None = None
        self._discovery_worker = None
        self._bootstrap_flash_worker = None
        self._deployment_worker = None
        self._bootstrap_service = BootstrapConfigService()
        self._registry = RobotRegistryService()
        self._build_ui()
        self._refresh_usb_ports()
        self._load_known_robots()

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

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.addWidget(self._build_deployment_panel())
        splitter.addWidget(self._build_console_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 500])
        root.addWidget(splitter, 1)

    def _build_deployment_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(9)

        bootstrap_group = QGroupBox("0 · First-Flash Setup")
        bootstrap_form = QFormLayout(bootstrap_group)
        bootstrap_form.setContentsMargins(10, 8, 10, 8)
        bootstrap_form.setVerticalSpacing(7)
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
        usb_row.setSpacing(6)
        self.usb_port_combo = QComboBox()
        self.usb_port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.usb_port_combo.setPlaceholderText("No USB/COM port detected")
        self.usb_port_combo.currentIndexChanged.connect(self._refresh_bootstrap_flash_enabled)
        usb_row.addWidget(self.usb_port_combo, 1)
        self.refresh_usb_button = QPushButton("Refresh USB")
        self.refresh_usb_button.setToolTip("Refresh USB/COM devices visible to Windows.")
        self.refresh_usb_button.clicked.connect(self._refresh_usb_ports)
        usb_row.addWidget(self.refresh_usb_button)
        self.generate_bootstrap_button = QPushButton("Generate Config")
        self.generate_bootstrap_button.clicked.connect(self.generate_bootstrap)
        usb_row.addWidget(self.generate_bootstrap_button)
        self.flash_bootstrap_button = QPushButton("Flash via USB")
        self.flash_bootstrap_button.setEnabled(False)
        self.flash_bootstrap_button.clicked.connect(self.flash_bootstrap)
        usb_row.addWidget(self.flash_bootstrap_button)
        bootstrap_form.addRow("USB Port:", usb_row)
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
        layout.setSpacing(9)

        serial_group = QGroupBox("USB Serial Console")
        serial_layout = QVBoxLayout(serial_group)
        serial_layout.setContentsMargins(10, 8, 10, 8)
        self.serial_console = SerialConsoleWidget(serial_group)
        serial_layout.addWidget(self.serial_console)
        layout.addWidget(serial_group, 3)

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
        self.output_label.setMinimumHeight(180)
        self.output_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        log_layout.addWidget(self.output_label, 1)
        layout.addWidget(log_group, 2)
        return panel

    @staticmethod
    def _console_font():
        from PySide6.QtGui import QFont
        return QFont("Courier New", 9)

    def _load_known_robots(self):
        self._robots = list(self._registry.robots())
        self._render_robot_combo(
            preferred_device_id=self._registry.selected_device_id,
            select_first_if_none=False,
        )
        if self._registry.load_error:
            self.robot_status.setText("Robot registry could not be loaded; starting with an empty registry.")
            self.robot_details.setText(self._registry.load_error)
            self.robot_details.setStyleSheet("color: #b36b00;")
        elif self._robots:
            self.robot_status.setText(
                f"{len(self._robots)} known robot(s). Click Discover to refresh Online/Offline state."
            )
        else:
            self.robot_status.setText("No known robots. Click Discover after the robot joins Wi-Fi.")

    def _render_robot_combo(
        self,
        *,
        preferred_device_id: str | None = None,
        select_first_if_none: bool = False,
    ) -> None:
        self._robots = list(self._registry.robots())
        target_id = preferred_device_id or self._registry.selected_device_id
        self.robot_combo.blockSignals(True)
        self.robot_combo.clear()
        for item in self._robots:
            robot = item.robot
            if item.online:
                readiness = "Ready" if robot.ready else "Not ready"
                state = f"Online · {readiness}"
            else:
                state = "Offline"
            self.robot_combo.addItem(
                f"{item.display_label} — {state}", item.device_id
            )

        index = self.robot_combo.findData(target_id) if target_id else -1
        if index < 0 and select_first_if_none and self.robot_combo.count():
            index = 0
        self.robot_combo.setCurrentIndex(index)
        self.robot_combo.blockSignals(False)
        device_id = self.robot_combo.itemData(index) if index >= 0 else None
        self._apply_selected_device(device_id, persist=bool(device_id))

    def _apply_selected_device(self, device_id: str | None, *, persist: bool) -> None:
        self._selected = self._registry.get(device_id)
        if persist:
            try:
                self._registry.set_selected(device_id)
            except RobotRegistryError as exc:
                self.result_label.setText(f"Robot selection could not be saved: {exc}")
                self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
        self._render_selected_details()

    def _render_selected_details(self) -> None:
        if self._selected is None:
            self.robot_status.setText("No robot selected")
            self.robot_details.setText("")
            self.robot_details.setStyleSheet("color: #666666;")
            self._refresh_deploy_enabled()
            return

        item = self._selected
        robot = item.robot
        capabilities = ", ".join(
            name.replace("_", " ") for name, enabled in robot.capabilities.items() if enabled
        ) or "None"
        if item.online:
            state = f"● Online · {'Ready' if robot.ready else 'Not ready'}"
        else:
            state = "○ Offline"
        self.robot_status.setText(f"{state} | {robot.hostname} | {robot.ip}")
        last_seen = item.last_seen_utc or "Never observed online in this registry"
        self.robot_details.setText(
            f"Device ID: {robot.device_id}\n"
            f"Target: {robot.target}   Firmware: {robot.firmware}\n"
            f"OTA: {'Available' if robot.ota else 'Unavailable'}\n"
            f"Last seen: {last_seen}\n"
            f"Capabilities: {capabilities}"
        )
        self.robot_details.setStyleSheet("color: #666666;")
        self._refresh_deploy_enabled()

    def _refresh_usb_ports(self):
        """Populate first-flash choices from the same Qt serial inventory as the console."""
        previous = self.usb_port_combo.currentData()
        self.usb_port_combo.blockSignals(True)
        self.usb_port_combo.clear()
        for port, description in SerialConsoleService.available_ports():
            label = f"{port} — {description}" if description else port
            self.usb_port_combo.addItem(label, port)
        if self.usb_port_combo.count():
            index = self.usb_port_combo.findData(previous) if previous else -1
            self.usb_port_combo.setCurrentIndex(index if index >= 0 else 0)
        self.usb_port_combo.blockSignals(False)
        self._refresh_bootstrap_flash_enabled()
        if not self.usb_port_combo.count() and self._bootstrap_path is not None:
            self.bootstrap_status.setText(
                "No USB/COM port is visible. Reconnect the robot or install the board USB/UART driver, then Refresh USB."
            )
            self.bootstrap_status.setStyleSheet("font-weight: bold; color: #b36b00;")

    def _selected_usb_port(self) -> str:
        value = self.usb_port_combo.currentData()
        return str(value).strip() if value else ""

    def _refresh_bootstrap_flash_enabled(self):
        running = bool(self._bootstrap_flash_worker and self._bootstrap_flash_worker.isRunning())
        self.flash_bootstrap_button.setEnabled(
            self._bootstrap_path is not None and bool(self._selected_usb_port()) and not running
        )

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
        self._refresh_usb_ports()
        self.bootstrap_status.setText(
            "✓ First-flash configuration ready.\n"
            f"Bootstrap artifact: {path}\n"
            "Select a detected USB/COM port and click Flash via USB."
        )
        self.bootstrap_status.setStyleSheet("font-weight: bold; color: green;")

    def flash_bootstrap(self):
        if self._bootstrap_path is None:
            return
        if self._bootstrap_flash_worker and self._bootstrap_flash_worker.isRunning():
            return
        usb_port = self._selected_usb_port()
        if not usb_port:
            QMessageBox.warning(
                self,
                "USB port required",
                "No USB/COM port is selected. Reconnect the robot or install its USB/UART driver, then Refresh USB.",
            )
            return
        self.generate_bootstrap_button.setEnabled(False)
        self.flash_bootstrap_button.setEnabled(False)
        self.refresh_usb_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.progress.setVisible(True)
        self.result_label.setText("Building and flashing first-boot firmware with PlatformIO...")
        self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
        self.bootstrap_status.setText(
            f"PlatformIO is building and uploading over {usb_port}. "
            "Keep the robot connected until the upload completes."
        )
        self.set_logs(f"PlatformIO first-flash in progress on {usb_port}...\n")
        self._bootstrap_flash_worker = _BootstrapFlashWorker(
            self._bootstrap_path, usb_port
        )
        self._bootstrap_flash_worker.output.connect(self.append_logs)
        self._bootstrap_flash_worker.completed.connect(self._on_bootstrap_flash_finished)
        self._bootstrap_flash_worker.finished.connect(self._bootstrap_flash_finished)
        self._bootstrap_flash_worker.start()

    def _bootstrap_flash_finished(self):
        self.progress.setVisible(False)
        self.generate_bootstrap_button.setEnabled(True)
        self.refresh_usb_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self._refresh_usb_ports()
        self._refresh_deploy_enabled()

    def _on_bootstrap_flash_finished(self, result):
        self.set_logs(result.output or "")
        if result.success:
            if result.verified_robot:
                try:
                    self._registry.upsert(result.verified_robot, online=True)
                    self._registry.set_selected(result.verified_robot.device_id)
                except RobotRegistryError as exc:
                    self.result_label.setText(f"First flash succeeded, but robot registry update failed: {exc}")
                    self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
                self._render_robot_combo(
                    preferred_device_id=result.verified_robot.device_id,
                    select_first_if_none=False,
                )
                self.bootstrap_status.setText(
                    "✓ First flash complete and new robot uniquely identified.\n"
                    f"Robot: {result.verified_robot.display_label} @ {result.verified_robot.ip}"
                )
            else:
                self.bootstrap_status.setText(
                    "✓ First flash completed. "
                    f"{result.error or 'Click Discover and select the flashed robot by identity.'}"
                )
            self.bootstrap_status.setStyleSheet("font-weight: bold; color: green;")
            if not result.verified_robot:
                self.result_label.setText("✓ First-flash upload completed; discover the robot to bind its identity.")
                self.result_label.setStyleSheet("font-weight: bold; color: green;")
            elif not self.result_label.styleSheet().endswith("#b36b00;"):
                self.result_label.setText("✓ First-flash upload completed and robot registered.")
                self.result_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.bootstrap_status.setText(f"✗ First-flash failed: {result.error or 'unknown error'}")
            self.bootstrap_status.setStyleSheet("font-weight: bold; color: red;")
            self.result_label.setText("First-flash failed. Check the PlatformIO output.")
            self.result_label.setStyleSheet("font-weight: bold; color: red;")

    def discover(self):
        if self._discovery_worker and self._discovery_worker.isRunning():
            return
        self.refresh_button.setEnabled(False)
        self._registry.mark_all_offline()
        self._render_robot_combo(
            preferred_device_id=self._registry.selected_device_id,
            select_first_if_none=False,
        )
        self.robot_status.setText("Searching for robots... known robots are temporarily marked Offline.")
        self.result_label.setText("Discovery in progress...")
        self.result_label.setStyleSheet("")
        self._refresh_deploy_enabled()
        self._discovery_worker = _DiscoveryWorker()
        self._discovery_worker.completed.connect(self._on_discovered)
        self._discovery_worker.failed.connect(self._on_discovery_failed)
        self._discovery_worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self._discovery_worker.start()

    def _on_discovered(self, robots):
        preferred = self._registry.selected_device_id
        save_error = None
        try:
            self._registry.merge_discovery(robots)
        except RobotRegistryError as exc:
            save_error = str(exc)
        self._render_robot_combo(
            preferred_device_id=preferred,
            select_first_if_none=True,
        )
        online = self._registry.online_count()
        offline = len(self._robots) - online
        if online:
            suffix = f"; {offline} known offline" if offline else ""
            self.robot_status.setText(f"Found {online} online robot(s){suffix}.")
            self.result_label.setText("Discovery complete. Select an online robot to deploy.")
            self.result_label.setStyleSheet("")
        elif self._robots:
            self.robot_status.setText(
                f"No robots online. {len(self._robots)} known robot(s) retained as Offline."
            )
            self.result_label.setText("Discovery complete — no known robot is currently online.")
            self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
        else:
            self.robot_status.setText(
                "No robot found. Make sure the robot is powered on and connected to the same Wi-Fi network."
            )
            self.result_label.setText("Discovery complete — no robot found.")
            self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
        if save_error:
            self.result_label.setText(f"Discovery succeeded, but registry persistence failed: {save_error}")
            self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
        self._refresh_deploy_enabled()

    def _on_discovery_failed(self, message):
        self._render_robot_combo(
            preferred_device_id=self._registry.selected_device_id,
            select_first_if_none=False,
        )
        self.robot_status.setText(
            f"Discovery failed: {message}. Known robots were retained and marked Offline."
        )
        self.result_label.setText("Discovery failed. Check the Wi-Fi network and try again.")
        self.result_label.setStyleSheet("font-weight: bold; color: red;")
        self._refresh_deploy_enabled()

    def _on_robot_selected(self, index):
        device_id = self.robot_combo.itemData(index) if 0 <= index < self.robot_combo.count() else None
        self._apply_selected_device(device_id, persist=bool(device_id))

    def _refresh_deploy_enabled(self):
        code_available = bool(self._code_provider().strip())
        item = self._selected
        robot = item.robot if item is not None else None
        self.deploy_button.setEnabled(
            item is not None and item.online and robot is not None and
            robot.ready and robot.ota and code_available and
            not (self._deployment_worker and self._deployment_worker.isRunning())
        )

    def deploy(self):
        item = self._selected
        robot: RobotInfo | None = item.robot if item is not None and item.online else None
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
        self.set_logs("Compiling, building and uploading. Please wait...\n")
        self._deployment_worker = _DeploymentWorker(
            code, robot, ssid, wifi_password, ota_password
        )
        self._deployment_worker.output.connect(self.append_logs)
        self._deployment_worker.completed.connect(self._on_deploy_finished)
        self._deployment_worker.finished.connect(self._deployment_finished)
        self._deployment_worker.start()

    def _deployment_finished(self):
        self.progress.setVisible(False)
        self.refresh_button.setEnabled(True)
        self._refresh_deploy_enabled()

    def _on_deploy_finished(self, result):
        self.set_logs(result.output or "")
        if result.success:
            verified = result.verified_robot
            if verified is not None:
                try:
                    self._registry.upsert(verified, online=True)
                    self._registry.set_selected(verified.device_id)
                except RobotRegistryError as exc:
                    self.result_label.setText(f"Deployment verified, but registry update failed: {exc}")
                    self.result_label.setStyleSheet("font-weight: bold; color: #b36b00;")
                self._render_robot_combo(
                    preferred_device_id=verified.device_id,
                    select_first_if_none=False,
                )
                if not self.result_label.styleSheet().endswith("#b36b00;"):
                    self.result_label.setText(
                        f"✓ Deployment verified — {verified.display_label} is ready and running."
                    )
                    self.result_label.setStyleSheet("font-weight: bold; color: green;")
            else:
                self.result_label.setText("✓ Deployment completed.")
                self.result_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.result_label.setText(f"✗ {result.error or 'Deployment failed.'}")
            self.result_label.setStyleSheet("font-weight: bold; color: red;")
        self._refresh_deploy_enabled()

    def set_logs(self, text: str):
        """Replace deployment logs and move the viewer to the newest output."""
        self.output_label.setPlainText(text or "")
        self.output_label.verticalScrollBar().setValue(self.output_label.verticalScrollBar().maximum())

    def append_logs(self, text: str):
        """Append live deployment output without stealing the user's scroll position."""
        if not text:
            return
        scrollbar = self.output_label.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 2
        cursor = self.output_label.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_label.setTextCursor(cursor)
        self.output_label.insertPlainText(text)
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self):
        self.output_label.clear()

    def copy_logs(self):
        self.output_label.selectAll()
        self.output_label.copy()
        self.output_label.moveCursor(self.output_label.textCursor().MoveOperation.End)

    def refresh_code_state(self):
        """Re-evaluate whether the current editor has code ready to deploy."""
        self._refresh_deploy_enabled()
