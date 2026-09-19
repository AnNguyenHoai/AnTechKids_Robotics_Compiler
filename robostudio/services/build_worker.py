"""
BuildWorker – non-blocking compiler contract runner using QProcess.

The compiler process always runs from the disposable workspace that owns the
request/source files. Compiler-contract JSON is an internal machine interface;
RoboStudio presents a concise human-readable compile result instead of dumping
that JSON into the Build Output panel.
"""

import json
import shutil
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal


CONTRACT_SCHEMA = "antechkids.robostudio.compiler-contract"
CONTRACT_VERSION = 1


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
        self._stdout_chunks = []
        self._stderr_chunks = []

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
        """Start the compiler process from external compiler state."""
        env_list = [f"{k}={v}" for k, v in self.env.items()]
        self.process.setEnvironment(env_list)
        self.process.setWorkingDirectory(str(self._workspace()))
        self.process.start(self.command[0], self.command[1:])

    def _on_stdout(self):
        data = self.process.readAllStandardOutput()
        text = data.data().decode("utf-8", errors="replace")
        self._stdout_chunks.append(text)
        # stdout belongs to the stable compiler contract and is intentionally
        # buffered until completion so raw JSON never leaks into the user log.

    def _on_stderr(self):
        data = self.process.readAllStandardError()
        text = data.data().decode("utf-8", errors="replace")
        self._stderr_chunks.append(text)
        # stderr may contain useful runtime diagnostics, so keep it live.
        if text:
            self.output_received.emit(text)

    def _on_finished(self, exit_code, exit_status):
        stdout = "".join(self._stdout_chunks)
        stderr = "".join(self._stderr_chunks)
        self._cleanup_temp_state()

        if exit_status == QProcess.CrashExit:
            self.error_occurred.emit("Compiler process crashed.")
            return

        details, summary = self.format_result(
            stdout=stdout,
            stderr=stderr,
            success=(exit_code == 0),
        )
        if details:
            self.output_received.emit(details if details.endswith("\n") else details + "\n")
        self.build_finished.emit(exit_code == 0, summary)

    def _on_process_error(self, error):
        self._cleanup_temp_state()
        msg = self.process.errorString()
        self.error_occurred.emit(f"Compiler process error: {msg}")

    @staticmethod
    def _parse_contract(stdout: str):
        """Return compiler-contract JSON when stdout is exactly that contract."""
        text = stdout.strip()
        if not text:
            return None
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(payload, dict):
            return None
        if payload.get("schema") != CONTRACT_SCHEMA:
            return None
        if payload.get("contract_version") != CONTRACT_VERSION:
            return None
        return payload

    @staticmethod
    def _contract_summary(payload: dict, success: bool) -> str:
        status = payload.get("status")
        contract_success = success and status == "PASS"
        if contract_success:
            lines = ["✅ Compile successful"]
            instruction_count = payload.get("instruction_count")
            if isinstance(instruction_count, int):
                lines.append(f"Instructions: {instruction_count}")
            lines.append("Robot program generated successfully.")
            return "\n".join(lines)

        lines = ["❌ Compile failed"]
        error_code = payload.get("error_code")
        error_message = payload.get("error_message")
        if error_code and error_message:
            lines.append(f"[{error_code}] {error_message}")
        elif error_message:
            lines.append(str(error_message))
        elif error_code:
            lines.append(f"Error code: {error_code}")
        else:
            lines.append("Compiler returned an unsuccessful contract response.")
        return "\n".join(lines)

    @classmethod
    def format_result(cls, stdout: str, stderr: str, success: bool):
        """Return (visible details, concise summary) for RoboStudio's log UI.

        Stable compiler-contract JSON stays machine-readable internally and is
        converted to a short user-facing summary. Unknown/non-contract output
        remains visible so legacy or infrastructure failures are still
        diagnosable.
        """
        payload = cls._parse_contract(stdout)
        if payload is not None:
            return "", cls._contract_summary(payload, success)

        combined = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
        lines = combined.splitlines()
        if success:
            summary = "✅ Compile completed"
        else:
            error_lines = [
                line
                for line in lines
                if "error" in line.lower()
                or "exception" in line.lower()
                or "failed" in line.lower()
            ]
            if error_lines:
                summary = "❌ Compile failed\n" + "\n".join(error_lines[:3])
            else:
                tail = lines[-5:] if len(lines) > 5 else lines
                summary = "❌ Compile failed"
                if tail:
                    summary += "\n" + "\n".join(tail)
        return combined, summary
