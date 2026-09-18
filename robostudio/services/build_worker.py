"""
BuildWorker – non-blocking build using QProcess.

The compiler process always runs from the disposable workspace that owns the
request/source files. In packaged mode the environment has already been sealed
by BuildService, so neither CWD nor mutable compiler state points at the
RoboStudio installation directory.
"""

import os
import shutil
from pathlib import Path
from PySide6.QtCore import QObject, QProcess, Signal


class BuildWorker(QObject):
    output_received = Signal(str)
    build_finished = Signal(bool, str)
    error_occurred = Signal(str)

    def __init__(self, command, env, temp_file_path):
        super().__init__()
        self.command = command
        self.env = env
        self.temp_file = temp_file_path
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_process_error)
        self._log_lines = []

    def _workspace(self) -> Path:
        return Path(self.temp_file).expanduser().resolve().parent

    def _cleanup_temp_state(self) -> None:
        """Remove only BuildService-owned disposable compile workspaces."""
        source = Path(self.temp_file).expanduser()
        workspace = source.resolve().parent
        if workspace.name.startswith("robostudio-compile-"):
            shutil.rmtree(workspace, ignore_errors=True)
            return
        try:
            source.unlink()
        except OSError:
            pass

    def start(self):
        """Start the build process from external compiler state."""
        env_list = [f"{k}={v}" for k, v in self.env.items()]
        self.process.setEnvironment(env_list)
        self.process.setWorkingDirectory(str(self._workspace()))
        self.process.start(self.command[0], self.command[1:])

    def _on_stdout(self):
        data = self.process.readAllStandardOutput()
        text = data.data().decode("utf-8", errors="replace")
        self._log_lines.append(text)
        self.output_received.emit(text)

    def _on_stderr(self):
        data = self.process.readAllStandardError()
        text = data.data().decode("utf-8", errors="replace")
        self._log_lines.append(text)
        self.output_received.emit(text)

    def _on_finished(self, exit_code, exit_status):
        self._cleanup_temp_state()

        if exit_status == QProcess.CrashExit:
            self.error_occurred.emit("Process crashed.")
            return

        full_log = "".join(self._log_lines)
        if exit_code == 0:
            summary = self._extract_summary(full_log, success=True)
            self.build_finished.emit(True, summary)
        else:
            summary = self._extract_summary(full_log, success=False)
            self.build_finished.emit(False, summary)

    def _on_process_error(self, error):
        self._cleanup_temp_state()
        msg = self.process.errorString()
        self.error_occurred.emit(f"Process error: {msg}")

    def _extract_summary(self, log, success):
        """Extract a human-friendly summary from the full log."""
        lines = log.splitlines()
        if success:
            if "Compiled successfully" in log or "OK" in log:
                return "✅ Build successful"
            return "✅ Build completed"

        error_lines = [
            line
            for line in lines
            if "error" in line.lower()
            or "exception" in line.lower()
            or "failed" in line.lower()
        ]
        if error_lines:
            return "❌ Build failed\n" + "\n".join(error_lines[:3])
        tail = lines[-5:] if len(lines) > 5 else lines
        return "❌ Build failed\n" + "\n".join(tail)
