"""
BuildWorker – non‑blocking build using QProcess
"""

import os
from PySide6.QtCore import QObject, QProcess, Signal, QByteArray


class BuildWorker(QObject):
    # Signals
    output_received = Signal(str)          # real‑time log line
    build_finished = Signal(bool, str)     # success, summary_message
    error_occurred = Signal(str)           # critical error (e.g., command not found)

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

        # Log accumulation (for summary)
        self._log_lines = []

    def start(self):
        """Start the build process."""
        # Set environment
        env_list = [f"{k}={v}" for k, v in self.env.items()]
        self.process.setEnvironment(env_list)
        self.process.setWorkingDirectory(os.getcwd())
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
        # Clean up temp file
        try:
            os.unlink(self.temp_file)
        except:
            pass

        if exit_status == QProcess.CrashExit:
            self.error_occurred.emit("Process crashed.")
            return

        # Generate summary
        full_log = "".join(self._log_lines)
        if exit_code == 0:
            summary = self._extract_summary(full_log, success=True)
            self.build_finished.emit(True, summary)
        else:
            summary = self._extract_summary(full_log, success=False)
            self.build_finished.emit(False, summary)

    def _on_process_error(self, error):
        # Handle errors like FailedToStart
        try:
            os.unlink(self.temp_file)
        except:
            pass
        msg = self.process.errorString()
        self.error_occurred.emit(f"Process error: {msg}")

    def _extract_summary(self, log, success):
        """
        Extract a human‑friendly summary from the full log.
        """
        lines = log.splitlines()
        if success:
            # Look for "Build completed." or "Compiled successfully" etc.
            if "Compiled successfully" in log or "OK" in log:
                return "✅ Build successful"
            return "✅ Build completed"

        # Failure: try to find error lines
        error_lines = [l for l in lines if "error" in l.lower() or "exception" in l.lower() or "failed" in l.lower()]
        if error_lines:
            # Take first few errors
            top = error_lines[:3]
            return "❌ Build failed\n" + "\n".join(top)
        # If no obvious error, show last few lines
        tail = lines[-5:] if len(lines) > 5 else lines
        return "❌ Build failed\n" + "\n".join(tail)