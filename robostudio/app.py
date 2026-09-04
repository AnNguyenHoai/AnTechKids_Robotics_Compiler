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


# List of example programs (name -> code)
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

        # Services
        self.build_service = BuildService()
        self.firmware_service = FirmwareService()
        self.hardware_config_service = HardwareConfigService()
        self._example_actions = {}

        # Build worker
        self.worker = None
        self.is_building = False

        # Check firmware on startup
        self._check_firmware()

        # Connect signals
        self.ui.compile_button.clicked.connect(self.on_compile)
        self.ui.code_editor.textChanged.connect(self._refresh_capability_status)
        self.ui.hardware_tab.configuration_saved.connect(self._refresh_capability_status)
        self.ui.open_firmware_button.clicked.connect(self.on_open_firmware)
        self.ui.about_action.triggered.connect(self.on_about)

        # Setup File menu
        self._setup_file_menu()

        # Build Examples menu
        self._build_examples_menu()

        # Initial capability state is part of the editor contract (H25-J).
        self._refresh_capability_status()

        # Set initial status
        self.set_status("Ready", color="green")

    def _setup_file_menu(self):
        """Add Open action to File menu."""
        # Find the File menu
        file_menu = self.ui.menubar.findChild(QMenu, "menuFile")
        if file_menu is None:
            # Fallback: use the first menu
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
        """Open a .py file and load its content into the editor."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open RoboSim Code",
            "",
            "Python Files (*.py);;All Files (*.*)"
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
        """If firmware not found, ask user to select it."""
        fw_path = self.firmware_service.get_firmware_path()
        if fw_path is None:
            QMessageBox.information(
                self,
                "Firmware Not Found",
                "Please select the main.ino (or RobotVM.ino) file for your robot."
            )
            self._browse_firmware()

    def _browse_firmware(self):
        """Open file dialog to select firmware .ino file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Firmware Project (main.ino or RobotVM.ino)",
            "",
            "Arduino Files (*.ino);;All Files (*.*)"
        )
        if file_path:
            self.firmware_service.set_firmware_path(Path(file_path))
            self.set_status("Firmware configured", color="green")
        else:
            # User cancelled, but we'll allow them to continue
            pass

    def _build_examples_menu(self):
        """Populate the Examples menu with actions."""
        for name, code in EXAMPLES.items():
            action = self.ui.examples_menu.addAction(name)
            action.triggered.connect(lambda checked, c=code: self._load_example(c))
            self._example_actions[name] = action
        self._refresh_example_capabilities()

    def _refresh_capability_status(self):
        """Refresh the editor's hardware capability view without compiling."""
        try:
            config = self.hardware_config_service.load()
        except Exception as exc:
            self.ui.capability_summary.setText("Hardware capability: unavailable")
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: red;")
            self.ui.capability_details.setText(f"Failed to load hardware configuration: {exc}")
            return

        source = self.ui.code_editor.toPlainText()
        analysis = ProgramCapabilityAnalyzer.analyze(source)
        self._set_capability_labels(analysis, config)
        self._refresh_example_capabilities()

    def _set_capability_labels(self, analysis, config):
        """Render required vs configured capabilities in a compact status card."""
        if analysis.syntax_error:
            self.ui.capability_summary.setText("Hardware capability: waiting for valid Python")
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: #b36b00;")
            self.ui.capability_details.setText(
                "Complete the program syntax to analyze its hardware requirements."
            )
            return

        names = {device.device_id: device.display_name for device in DeviceRegistry.all()}
        required = [names[d] for d in analysis.required_devices]
        configured = [names[d] for d in config.enabled_devices()]
        missing = [names[d] for d in analysis.missing_devices(config)]

        if missing:
            self.ui.capability_summary.setText(
                "Hardware capability: MISSING — " + ", ".join(missing)
            )
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: red;")
            if not self.is_building:
                self.ui.compile_button.setEnabled(False)
                self.ui.compile_button.setToolTip(
                    "Enable the missing hardware in the Hardware tab before compiling."
                )
        elif required:
            if not self.is_building:
                self.ui.compile_button.setEnabled(True)
                self.ui.compile_button.setToolTip("Compile program")
            self.ui.capability_summary.setText("Hardware capability: READY")
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.ui.capability_summary.setText("Hardware capability: no registered requirements")
            self.ui.capability_summary.setStyleSheet("font-weight: bold; color: #666666;")
            if not self.is_building:
                self.ui.compile_button.setEnabled(True)
                self.ui.compile_button.setToolTip("Compile program")

        required_text = ", ".join(required) if required else "None"
        configured_text = ", ".join(configured) if configured else "None"
        self.ui.capability_details.setText(
            f"Program requires: {required_text}  |  Configured: {configured_text}"
        )

    def _refresh_example_capabilities(self):
        """Mark examples that cannot run with the current hardware configuration."""
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
        """Load example code into the editor."""
        self.ui.code_editor.setPlainText(code)

    def on_compile(self):
        """Handle Compile button click."""
        if self.is_building:
            return

        code = self.ui.code_editor.toPlainText()
        if not code.strip():
            self.ui.build_output.setPlainText("Error: No code to compile.")
            self.set_status("Failed", color="red")
            return

        # Clear output
        self.ui.build_output.clear()
        self.set_status("Building...", color="blue")
        self.is_building = True
        self.ui.compile_button.setEnabled(False)
        self.ui.compile_button.setText("Building...")
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        # Prepare command
        try:
            cmd, env, temp_file = self.build_service.get_command(code)
        except Exception as e:
            self._build_finished(success=False, summary=f"Error preparing build: {e}")
            return

        # Create and start worker
        self.worker = BuildWorker(cmd, env, temp_file)
        self.worker.output_received.connect(self._on_output)
        self.worker.build_finished.connect(self._build_finished)
        self.worker.error_occurred.connect(self._build_error)
        self.worker.start()

    def _on_output(self, text):
        """Append real‑time output to build log."""
        self.ui.build_output.insertPlainText(text)
        # Auto-scroll to bottom
        cursor = self.ui.build_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ui.build_output.setTextCursor(cursor)

    def _build_finished(self, success, summary):
        """Handle build completion."""
        self.is_building = False
        self.ui.compile_button.setEnabled(True)
        self.ui.compile_button.setText("Compile")
        QApplication.restoreOverrideCursor()

        if success:
            self.set_status("Success", color="green")
            # Append summary
            self.ui.build_output.append("\n" + "="*40)
            self.ui.build_output.append(summary)
            self.ui.build_output.append("Arduino Ready – you can now upload.")
        else:
            self.set_status("Failed", color="red")
            self.ui.build_output.append("\n" + "="*40)
            self.ui.build_output.append(summary)
            self.ui.build_output.append("\nCheck the log above for details.")

    def _build_error(self, error_msg):
        """Handle critical worker errors."""
        self.is_building = False
        self.ui.compile_button.setEnabled(True)
        self.ui.compile_button.setText("Compile")
        QApplication.restoreOverrideCursor()
        self.set_status("Error", color="red")
        self.ui.build_output.append(f"\nError: {error_msg}")

    def on_open_firmware(self):
        """Open the firmware project."""
        try:
            self.firmware_service.open_firmware()
        except FileNotFoundError as e:
            # Show prompt to select firmware
            ret = QMessageBox.question(
                self,
                "Firmware Not Found",
                str(e) + "\n\nWould you like to locate the firmware file?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret == QMessageBox.Yes:
                self._browse_firmware()
                # Retry after selection
                try:
                    self.firmware_service.open_firmware()
                except Exception as e2:
                    QMessageBox.critical(self, "Error", f"Still unable to open: {e2}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open firmware:\n{str(e)}")

    def on_about(self):
        QMessageBox.about(
            self,
            "About RoboStudio",
            "RoboStudio MVP\n\n"
            "A simple launcher for Robot Compiler.\n"
            "Version: M4.2\n"
            "License: MIT"
        )

    def set_status(self, text, color="black"):
        """Update status label with color (green/red/blue/black)."""
        self.ui.status_label.setText(text)
        self.ui.status_label.setStyleSheet(f"font-weight: bold; color: {color};")