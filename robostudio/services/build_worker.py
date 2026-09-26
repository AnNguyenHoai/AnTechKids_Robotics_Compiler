"""BuildWorker – non-blocking compiler contract runner.

Compiler-contract JSON remains an internal machine interface. Successful output
artifacts are copied out of the disposable compiler workspace before cleanup so
RoboStudio can show useful, durable paths to the user.

The worker owns a background Qt thread, but launches the compiler with the same
Windows hidden-console policy as deployment. This prevents student-facing
terminal windows from flashing during Compile while keeping the UI responsive.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from tools import runtime_paths
from tools.deployment_runtime import (
    CLASSROOM_BUILD_TIMEOUT_SECONDS,
    windows_hidden_process_creation_flags,
)


CONTRACT_SCHEMA = "antechkids.robostudio.compiler-contract"
CONTRACT_VERSION = 1
ARTIFACT_FIELDS = (
    ("output", "Program header", "program.h"),
    ("report", "Compile report", "compile_report.json"),
    ("rewritten_source", "Rewritten source", "rewritten_source.py"),
)


class BuildWorker(QThread):
    output_received = Signal(str)
    build_finished = Signal(bool, str)
    error_occurred = Signal(str)

    def __init__(self, command, env, temp_file_path):
        super().__init__()
        self.command = command
        self.env = env
        self.temp_file = temp_file_path

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

    def run(self):
        """Run the compiler off the UI thread with a bounded classroom timeout."""
        kwargs: dict[str, object] = {
            "cwd": str(self._workspace()),
            "env": self.env,
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "check": False,
            "timeout": CLASSROOM_BUILD_TIMEOUT_SECONDS,
        }
        if os.name == "nt":
            kwargs["creationflags"] = windows_hidden_process_creation_flags()
        else:
            kwargs["start_new_session"] = True

        try:
            completed = subprocess.run(self.command, **kwargs)
        except subprocess.TimeoutExpired:
            self._cleanup_temp_state()
            self.error_occurred.emit(
                "Compiler process timed out after "
                f"{int(CLASSROOM_BUILD_TIMEOUT_SECONDS)} seconds. "
                "This computer may be unusually slow; close heavy applications and retry."
            )
            return
        except OSError as exc:
            self._cleanup_temp_state()
            self.error_occurred.emit(f"Compiler process error: {exc}")
            return

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""

        payload = self._parse_contract(stdout)
        if payload is not None and completed.returncode == 0 and payload.get("status") == "PASS":
            try:
                payload = self._publish_contract_artifacts(payload)
                stdout = json.dumps(payload)
            except OSError as exc:
                stderr += f"\nWARNING: unable to publish compiler artifacts: {exc}\n"

        details, summary = self.format_result(
            stdout=stdout,
            stderr=stderr,
            success=(completed.returncode == 0),
        )
        self._cleanup_temp_state()
        if details:
            self.output_received.emit(details if details.endswith("\n") else details + "\n")
        self.build_finished.emit(completed.returncode == 0, summary)

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
            error_lines = [
                line
                for line in lines
                if "error" in line.lower() or "exception" in line.lower() or "failed" in line.lower()
            ]
            if error_lines:
                summary = "❌ Compile failed\n" + "\n".join(error_lines[:3])
            else:
                tail = lines[-5:] if len(lines) > 5 else lines
                summary = "❌ Compile failed"
                if tail:
                    summary += "\n" + "\n".join(tail)
        return combined, summary
