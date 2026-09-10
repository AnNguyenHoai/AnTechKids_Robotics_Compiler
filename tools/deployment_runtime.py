"""Runtime helpers for reliable RoboStudio deployment subprocesses.

The deployment boundary must not depend on a shell command being available on
PATH and must not leave a GUI operation blocked forever. This module provides a
small, UI-independent process runner with bounded execution and line-oriented
output streaming.
"""
from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from tools.runtime_paths import platformio_command as resolve_platformio_command

DEFAULT_PROCESS_TIMEOUT_SECONDS = 300.0


class DeploymentRuntimeError(RuntimeError):
    """Raised when a deployment subprocess cannot be started or times out."""


@dataclass(frozen=True)
class ProcessResult:
    """Completed process information plus the complete combined output."""

    returncode: int
    output: str


def platformio_command(*args: str) -> list[str]:
    """Build the PlatformIO command through the RoboStudio runtime resolver.

    A packaged RoboStudio build uses its private runtime/bin tool. Source
    development retains the existing interpreter-based PlatformIO fallback.
    The deployment layer therefore never performs PATH-based executable
    lookup itself.
    """
    return resolve_platformio_command(*args)


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_PROCESS_TIMEOUT_SECONDS,
    on_output: Callable[[str], None] | None = None,
) -> ProcessResult:
    """Run a process, stream combined output, and enforce a hard deadline.

    ``subprocess.run(..., timeout=...)`` is not sufficient for RoboStudio's
    live console because it buffers output until the child exits. A dedicated
    reader thread drains stdout while the caller enforces the deadline.
    """
    if not command:
        raise ValueError("Deployment command must not be empty.")
    if timeout <= 0:
        raise ValueError("Deployment process timeout must be greater than zero.")

    try:
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            env=dict(env) if env is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        raise DeploymentRuntimeError(
            f"Unable to start deployment command: {exc}"
        ) from exc

    output: list[str] = []
    reader_done = threading.Event()

    def read_output() -> None:
        try:
            assert process.stdout is not None
            for line in process.stdout:
                output.append(line)
                if on_output is not None:
                    on_output(line)
        finally:
            reader_done.set()

    reader = threading.Thread(target=read_output, name="deployment-output", daemon=True)
    reader.start()

    deadline = time.monotonic() + timeout
    while process.poll() is None:
        if time.monotonic() >= deadline:
            process.terminate()
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            reader_done.wait(timeout=2.0)
            raise DeploymentRuntimeError(
                f"Deployment command timed out after {timeout:.0f}s."
            )
        time.sleep(0.05)

    reader_done.wait(timeout=2.0)
    return ProcessResult(process.returncode, "".join(output))
