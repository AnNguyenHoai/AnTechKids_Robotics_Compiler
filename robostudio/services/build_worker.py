"""BuildWorker – non-blocking compiler contract runner using QProcess.

Compiler-contract JSON remains an internal machine interface. Successful output
artifacts are copied out of the disposable compiler workspace before cleanup so
RoboStudio can show useful, durable paths to the user.
"""

import json
import shutil
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal
from tools import runtime_paths


CONTRACT_SCHEMA = "antechkids.robostudio.compiler-contract"
CONTRACT_VERSION = 1
ARTIFACT_FIELDS = (
    ("output", "Program header", "program.h"),
    ("report", "Compile report", "compile_report.json"),
    ("rewritten_source", "Rewritten source", "rewritten_source.py"),
)


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
        env_list = [f"{k}={v}" for k, v in self.env.items()]
        self.process.setEnvironment(env_list)
        self.process.setWorkingDirectory(str(self._workspace()))
        self.process.start(self.command[0], self.command[1:])

    def _on_stdout(self):
        data = self.process.readAllStandardOutput()
        self._stdout_chunks.append(data.data().decode("utf-8", errors="replace"))

    def _on_stderr(self):
        data = self.process.readAllStandardError()
        text = data.data().decode("utf-8", errors="replace")
        self._stderr_chunks.append(text)
        if text:
            self.output_received.emit(text)

    @staticmethod
    def _parse_contract(stdout: str):
        text = stdout.strip()
        if not text:
            return None
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(payload, dict):
            return None
        if payload.get("schema") != CONTRACT_SCHEMA or payload.get("contract_version") != CONTRACT_VERSION:
            return None
        return payload

    @classmethod
    def _publish_contract_artifacts(cls, payload: dict) -> dict:
        """Copy successful compiler outputs to stable user state and rewrite paths.

        The compiler itself writes into a disposable workspace. Exposing those
        paths after deleting the workspace would be misleading, so only files
        that actually exist are published under ``artifacts/compile/latest``.
        """
        destination_root = runtime_paths.prepare_user_data_root() / "artifacts" / "compile" / "latest"
        destination_root.mkdir(parents=True, exist_ok=True)
        published = dict(payload)
        for field, _label, filename in ARTIFACT_FIELDS:
            value = payload.get(field)
            if not value:
                continue
            source = Path(str(value)).expanduser()
            if not source.is_file():
                continue
            destination = destination_root / filename
            shutil.copy2(source, destination)
            published[field] = str(destination.resolve())
        return published

    @staticmethod
    def _contract_summary(payload: dict, success: bool) -> str:
        status = payload.get("status")
        contract_success = success and status == "PASS"
        if contract_success:
            lines = ["✅ Compile successful"]
            instruction_count = payload.get("instruction_count")
            if isinstance(instruction_count, int):
                lines.append(f"Instructions: {instruction_count}")
            artifacts = []
            for field, label, _filename in ARTIFACT_FIELDS:
                value = payload.get(field)
                if value:
                    artifacts.append(f"  {label}: {value}")
            if artifacts:
                lines.append("Output artifacts:")
                lines.extend(artifacts)
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

    def _on_finished(self, exit_code, exit_status):
        stdout = "".join(self._stdout_chunks)
        stderr = "".join(self._stderr_chunks)

        if exit_status == QProcess.CrashExit:
            self._cleanup_temp_state()
            self.error_occurred.emit("Compiler process crashed.")
            return

        payload = self._parse_contract(stdout)
        if payload is not None and exit_code == 0 and payload.get("status") == "PASS":
            try:
                payload = self._publish_contract_artifacts(payload)
                stdout = json.dumps(payload)
            except OSError as exc:
                stderr += f"\nWARNING: unable to publish compiler artifacts: {exc}\n"

        details, summary = self.format_result(stdout=stdout, stderr=stderr, success=(exit_code == 0))
        self._cleanup_temp_state()
        if details:
            self.output_received.emit(details if details.endswith("\n") else details + "\n")
        self.build_finished.emit(exit_code == 0, summary)

    def _on_process_error(self, error):
        self._cleanup_temp_state()
        self.error_occurred.emit(f"Compiler process error: {self.process.errorString()}")

    @classmethod
    def format_result(cls, stdout: str, stderr: str, success: bool):
        payload = cls._parse_contract(stdout)
        if payload is not None:
            return "", cls._contract_summary(payload, success)

        combined = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
        lines = combined.splitlines()
        if success:
            summary = "✅ Compile completed"
        else:
            error_lines = [line for line in lines if "error" in line.lower() or "exception" in line.lower() or "failed" in line.lower()]
            if error_lines:
                summary = "❌ Compile failed\n" + "\n".join(error_lines[:3])
            else:
                tail = lines[-5:] if len(lines) > 5 else lines
                summary = "❌ Compile failed"
                if tail:
                    summary += "\n" + "\n".join(tail)
        return combined, summary
