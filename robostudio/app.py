"""
RoboStudio Application – main controller
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QTextCursor

from ui.main_window import Ui_MainWindow
from services.build_service import BuildService
from services.firmware_service import FirmwareService
from services.build_worker import BuildWorker


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

        # Build worker
        self.worker = None
        self.is_building = False

        # Check firmware on startup
        self._check_firmware()

        # Connect signals
        self.ui.compile_button.clicked.connect(self.on_compile)
        self.ui.open_firmware_button.clicked.connect(self.on_open_firmware)
        self.ui.about_action.triggered.connect(self.on_about)

        # Build Examples menu
        self._build_examples_menu()

        # Set initial status
        self.set_status("Ready", color="green")

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
        cursor.movePosition(QTextCursor.MoveOperation.End)
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