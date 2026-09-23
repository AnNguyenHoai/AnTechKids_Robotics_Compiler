"""
RoboStudio Application – main controller
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QApplication, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QTextCursor, QAction

from ui.main_window import Ui_MainWindow
from services.build_service import BuildService
from services.firmware_service import FirmwareService
from services.build_worker import BuildWorker
from domain.device_registry import DeviceRegistry
from domain.hardware_config_service import HardwareConfigService
from domain.program_capabilities import ProgramCapabilityAnalyzer
from domain.target_capability_view import TargetCapabilityService, TargetCapabilityViewError, required_capabilities


EXAMPLES = {
    "Motion (Forward)": """import rcu
import _thread

def task():
    rcu.SetMoveRunSecond("forward", 80, 1)

_thread.start_new_thread(task, ())
while True:
    pass
""",
    "LED Blink": """import rcu

rcu.Set3CLed(1, 1)
rcu.SetWaitForTime(0.5)
rcu.Set3CLed(1, 0)
""",
    "Buzzer Beep": """import rcu

rcu.SetMp3Play(1)
""",
    "Line Following (Basic)": """import rcu

while True:
    rcu.line_basis(60)
    rcu.SetWaitForTime(0.02)
""",
    "Ultrasonic Obstacle": """import rcu

while True:
    dist = rcu.GetUltrasound(1)
    if dist < 20:
        rcu.SetMoveStop()
    else:
        rcu.SetMoveRun("forward", 50)
    rcu.SetWaitForTime(0.1)
""",
    "Touch Stop": """import rcu

while True:
    if rcu.GetTouch(1):
        rcu.SetMoveStop()
    else:
        rcu.SetMoveRun("forward", 50)
    rcu.SetWaitForTime(0.05)
"""
}


class RoboStudioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.build_service = BuildService()
        self.firmware_service = FirmwareService()
        self.hardware_config_service = HardwareConfigService()
        self.target_capability_service = TargetCapabilityService.load()
        self._example_actions = {}
        self.worker = None
        self.is_building = False

        self._check_firmware()

        self.ui.compile_button.clicked.connect(self.on_compile)
        self.ui.code_editor.textChanged.connect(self._refresh_capability_status)
        self.ui.hardware_tab.configuration_saved.connect(self._refresh_capability_status)
        self.ui.target_combo.currentIndexChanged.connect(self._refresh_capability_status)
        # Keep the compatibility button connected for existing source contracts,
        # but expose firmware editing only from the Advanced menu in Phase 2.
        self.ui.open_firmware_button.clicked.connect(self.on_open_firmware)
        self.ui.open_firmware_action.triggered.connect(self.on_open_firmware)
        self.ui.about_action.triggered.connect(self.on_about)

        self._setup_file_menu()
        self._build_examples_menu()
        self._populate_targets()
        self._refresh_capability_status()
        self.set_status("Ready", color="green")

    def _setup_file_menu(self):
        file_menu = self.ui.menubar.findChild(QMenu, "menuFile")
        if file_menu is None:
            file_menu = self.ui.menubar.actions()[0].menu()

        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open RoboSim Code", "", "Python Files (*.py);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                self.ui.code_editor.setPlainText(code)
                self.set_status(f"Loaded: {Path(file_path).name}", color="green")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")

    def _check_firmware(self):
        fw_path = self.firmware_service.get_firmware_path()
        if fw_path is None:
            QMessageBox.information(
                self, "Firmware Not Found",
                "Please select the main.ino (or RobotVM.ino) file for your robot."
            )
            self._browse_firmware()

    def _browse_firmware(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Firmware Project (main.ino or RobotVM.ino)", "",
            "Arduino Files (*.ino);;All Files (*.*)"
        )
        if file_path:
            self.firmware_service.set_firmware_path(Path(file_path))
            self.set_status("Firmware configured", color="green")

    def _populate_targets(self):
        self.ui.target_combo.blockSignals(True)
        self.ui.target_combo.clear()
        for target_id in self.target_capability_service.target_ids():
            self.ui.target_combo.addItem(target_id.upper(), target_id)
        self.ui.target_combo.blockSignals(False)
        if self.ui.target_combo.count():
            self.ui.target_combo.setCurrentIndex(0)

    def _selected_target_id(self):
        return self.ui.target_combo.currentData()

    def _build_examples_menu(self):
        for name, code in EXAMPLES.items():
            action = self.ui.examples_menu.addAction(name)
            action.triggered.connect(lambda checked, c=code: self._load_example(c))
            self._example_actions[name] = action
        self._refresh_example_capabilities()

    def _refresh_capability_status(self):
        """Refresh hardware and selected-target capability status without compiling."""
        try:
            config = self.hardware_config_service.load()
        except Exception as exc:
            self.ui.capability_summary.setText("Hardware capability: unavailable")
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: red;")
            self.ui.capability_details.setText(f"Failed to load hardware configuration: {exc}")
            self.ui.target_capability_details.setText("")
            return

        source = self.ui.code_editor.toPlainText()
        analysis = ProgramCapabilityAnalyzer.analyze(source)
        self._set_capability_labels(analysis, config)
        self._refresh_target_capability(analysis)
        self._refresh_example_capabilities()

    def _set_capability_labels(self, analysis, config):
        names = {device.device_id: device.display_name for device in DeviceRegistry.all()}
        if analysis.syntax_error:
            self.ui.capability_summary.setText("Hardware capability: waiting for valid Python")
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: #b36b00;")
            self.ui.capability_details.setText("Complete the program syntax to analyze its hardware requirements.")
            return

        required = [names[d] for d in analysis.required_devices]
        configured = [names[d] for d in config.enabled_devices()]
        missing = [names[d] for d in analysis.missing_devices(config)]
        if missing:
            self.ui.capability_summary.setText("Hardware capability: MISSING — " + ", ".join(missing))
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: red;")
        elif required:
            self.ui.capability_summary.setText("Hardware capability: READY")
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.ui.capability_summary.setText("Hardware capability: no registered requirements")
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: #666666;")

        required_text = ", ".join(required) if required else "None"
        configured_text = ", ".join(configured) if configured else "None"
        self.ui.capability_details.setText(
            f"Program requires: {required_text}  |  Configured: {configured_text}"
        )

    def _refresh_target_capability(self, analysis):
        """Show whether the selected target supports the program's canonical capabilities."""
        if analysis.syntax_error:
            self.ui.target_capability_details.setText("Target capability: waiting for valid Python")
            self.ui.target_capability_details.setStyleSheet("color: #b36b00;")
            self._set_compile_enabled(False)
            return

        target_id = self._selected_target_id()
        if not target_id:
            self.ui.target_capability_details.setText("Target capability: no target selected")
            self.ui.target_capability_details.setStyleSheet("color: red;")
            self._set_compile_enabled(False)
            return

        try:
            required = required_capabilities(analysis.api_names)
            view = self.target_capability_service.evaluate(target_id, required)
        except TargetCapabilityViewError as exc:
            self.ui.target_capability_details.setText(f"Target capability: unavailable — {exc}")
            self.ui.target_capability_details.setStyleSheet("color: red;")
            self._set_compile_enabled(False)
            return

        self.ui.target_description.setText(view.description)
        if view.ready:
            self.ui.target_capability_details.setText(
                f"Target {target_id.upper()}: READY — supports all required capabilities."
            )
            self.ui.target_capability_details.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.ui.target_capability_details.setText(
                f"Target {target_id.upper()}: MISSING — " + ", ".join(view.missing)
            )
            self.ui.target_capability_details.setStyleSheet("font-weight: bold; color: red;")

        self._set_compile_enabled(view.ready and not self._hardware_requirements_missing(analysis))

    def _hardware_requirements_missing(self, analysis):
        try:
            config = self.hardware_config_service.load()
            return bool(analysis.missing_devices(config))
        except Exception:
            return True

    def _set_compile_enabled(self, enabled):
        if not self.is_building:
            self.ui.compile_button.setEnabled(enabled)
            self.ui.compile_button.setToolTip("Compile program" if enabled else "Resolve hardware and target capability requirements first")

    def _refresh_example_capabilities(self):
        if not self._example_actions:
            return
        try:
            config = self.hardware_config_service.load()
        except Exception:
            return
        for name, action in self._example_actions.items():
            analysis = ProgramCapabilityAnalyzer.analyze(EXAMPLES[name])
            missing = analysis.missing_devices(config)
            if missing:
                labels = {d.device_id: d.display_name for d in DeviceRegistry.all()}
                missing_names = ", ".join(labels[d] for d in missing)
                action.setEnabled(False)
                action.setToolTip(f"Unavailable: requires {missing_names}")
            else:
                action.setEnabled(True)
                action.setToolTip("Load example")

    def _load_example(self, code):
        self.ui.code_editor.setPlainText(code)

    def on_compile(self):
        if self.is_building:
            return
        code = self.ui.code_editor.toPlainText()
        if not code.strip():
            self.ui.build_output.setPlainText("Error: No code to compile.")
            self.set_status("Failed", color="red")
            return

        self.ui.build_output.setPlainText("Compiling RoboSim program...\n")
        self.set_status("Compiling...", color="blue")
        self.is_building = True
        self.ui.compile_button.setEnabled(False)
        self.ui.compile_button.setText("Compiling...")
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            cmd, env, temp_file = self.build_service.get_command(code)
        except Exception as e:
            self._build_finished(success=False, summary=f"Error preparing compile: {e}")
            return

        self.worker = BuildWorker(cmd, env, temp_file)
        self.worker.output_received.connect(self._on_output)
        self.worker.build_finished.connect(self._build_finished)
        self.worker.error_occurred.connect(self._build_error)
        self.worker.start()

    def _on_output(self, text):
        self.ui.build_output.insertPlainText(text)
        cursor = self.ui.build_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ui.build_output.setTextCursor(cursor)

    def _build_finished(self, success, summary):
        self.is_building = False
        self._refresh_capability_status()
        self.ui.compile_button.setText("Compile Program")
        QApplication.restoreOverrideCursor()
        self.ui.build_output.append("\n" + "="*40)
        self.ui.build_output.append(summary)
        if success:
            self.set_status("Compiled", color="green")
            self.ui.build_output.append("Ready for deployment to robot.")
        else:
            self.set_status("Failed", color="red")
            self.ui.build_output.append("\nCheck the compiler message above for details.")

    def _build_error(self, error_msg):
        self.is_building = False
        self._refresh_capability_status()
        self.ui.compile_button.setText("Compile Program")
        QApplication.restoreOverrideCursor()
        self.set_status("Error", color="red")
        self.ui.build_output.append(f"\nCompile error: {error_msg}")

    def on_open_firmware(self):
        try:
            self.firmware_service.open_firmware()
        except FileNotFoundError as e:
            ret = QMessageBox.question(
                self, "Firmware Not Found", str(e) + "\n\nWould you like to locate the firmware file?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret == QMessageBox.Yes:
                self._browse_firmware()
                try:
                    self.firmware_service.open_firmware()
                except Exception as e2:
                    QMessageBox.critical(self, "Error", f"Still unable to open: {e2}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open firmware:\n{str(e)}")

    def on_about(self):
        QMessageBox.about(
            self, "About RoboStudio",
            "RoboStudio\n\nRobot programming and deployment workspace.\nVersion: M4.2\nLicense: MIT"
        )

    def set_status(self, text, color="black"):
        self.ui.status_label.setText(text)
        self.ui.status_label.setStyleSheet(f"font-weight: bold; color: {color};")
