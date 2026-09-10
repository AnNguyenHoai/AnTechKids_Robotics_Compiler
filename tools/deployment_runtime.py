"""Runtime helpers for reliable RoboStudio deployment subprocesses.

The deployment boundary must not depend on a shell command being available on
PATH and must not leave a GUI operation blocked forever. This module provides a
small, UI-independent process runner with bounded execution and line-oriented
output streaming, plus an application-owned PlatformIO runtime environment.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from tools import runtime_paths
from tools.runtime_paths import platformio_command as resolve_platformio_command

DEFAULT_PROCESS_TIMEOUT_SECONDS = 300.0
PLATFORMIO_CORE_DIR_ENV = "PLATFORMIO_CORE_DIR"
PLATFORMIO_PLATFORMS_DIR_ENV = "PLATFORMIO_PLATFORMS_DIR"
PLATFORMIO_PACKAGES_DIR_ENV = "PLATFORMIO_PACKAGES_DIR"
PLATFORMIO_CACHE_DIR_ENV = "PLATFORMIO_CACHE_DIR"
PLATFORMIO_BUILD_CACHE_DIR_ENV = "PLATFORMIO_BUILD_CACHE_DIR"
PLATFORMIO_WORKSPACE_DIR_ENV = "PLATFORMIO_WORKSPACE_DIR"
PLATFORMIO_DISABLE_UPGRADE_CHECK_ENV = "PLATFORMIO_DISABLE_UPGRADE_CHECK"
PLATFORMIO_DISABLE_PROGRESSBAR_ENV = "PLATFORMIO_DISABLE_PROGRESSBAR"
PLATFORMIO_NO_ANSI_ENV = "PLATFORMIO_NO_ANSI"


class DeploymentRuntimeError(RuntimeError):
    """Raised when a deployment subprocess cannot be started or times out."""


@dataclass(frozen=True)
class ProcessResult:
    """Completed process information plus the complete combined output."""

    returncode: int
    output: str


def application_root() -> Path:
    """Resolve the application root through the deployment frozen-state seam.

    ``ROBOSTUDIO_HOME`` always wins, which gives packaged integrations and
    contract tests a deterministic root. When no override exists, a frozen
    deployment is rooted beside its executable. Source builds delegate to the
    canonical runtime-path implementation.
    """
    override = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if is_frozen():
        return Path(__import__("sys").executable).resolve().parent
    return runtime_paths.application_root()


def deployment_runtime_root() -> Path:
    """Return the immutable PlatformIO/deployment runtime root."""
    # Keep this function as the deployment-facing API while using the same
    # canonical runtime-path primitive as the tool resolver.
    return application_root() / "runtime" / "platformio"


def deployment_runtime_core_dir() -> Path:
    """Return the private PlatformIO Core data directory shipped by RoboStudio."""
    return deployment_runtime_root()


def deployment_runtime_environment(
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build the environment for a deployment subprocess.

    Frozen RoboStudio runs are completely isolated from the user's global
    PlatformIO installation. PlatformIO's documented directory environment
    variables are pointed at the application-owned runtime. Source builds keep
    their existing environment so the developer workflow remains unchanged.
    """
    env = dict(os.environ if base_env is None else base_env)
    if not is_frozen():
        return env

    core = deployment_runtime_core_dir()
    env.update(
        {
            PLATFORMIO_CORE_DIR_ENV: str(core),
            PLATFORMIO_PLATFORMS_DIR_ENV: str(core / "platforms"),
            PLATFORMIO_PACKAGES_DIR_ENV: str(core / "packages"),
            PLATFORMIO_CACHE_DIR_ENV: str(core / ".cache"),
            PLATFORMIO_BUILD_CACHE_DIR_ENV: str(core / "build-cache"),
            PLATFORMIO_WORKSPACE_DIR_ENV: str(core / "workspace"),
            PLATFORMIO_DISABLE_UPGRADE_CHECK_ENV: "true",
            PLATFORMIO_DISABLE_PROGRESSBAR_ENV: "true",
            PLATFORMIO_NO_ANSI_ENV: "true",
        }
    )
    return env


def validate_deployment_runtime() -> Path:
    """Validate that the packaged PlatformIO runtime has its required layout."""
    root = deployment_runtime_root()
    if not root.is_dir():
        raise DeploymentRuntimeError(f"RoboStudio deployment runtime is missing: {root}")
    if not (root / "platforms").is_dir():
        raise DeploymentRuntimeError(
            f"RoboStudio deployment runtime is missing platforms: {root / 'platforms'}"
        )
    if not (root / "packages").is_dir():
        raise DeploymentRuntimeError(
            f"RoboStudio deployment runtime is missing packages: {root / 'packages'}"
        )
    return root


def platformio_command(*args: str) -> list[str]:
    """Build the PlatformIO command through the RoboStudio runtime resolver."""
    return resolve_platformio_command(*args)


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_PROCESS_TIMEOUT_SECONDS,
    on_output: Callable[[str], None] | None = None,
) -> ProcessResult:
    """Run a process, stream combined output, and enforce a hard deadline."""
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
        raise DeploymentRuntimeError(f"Unable to start deployment command: {exc}") from exc

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
            raise DeploymentRuntimeError(f"Deployment command timed out after {timeout:.0f}s.")
        time.sleep(0.05)

    reader_done.wait(timeout=2.0)
    return ProcessResult(process.returncode, "".join(output))


# Keep this local alias for compatibility with existing tests that patch the
# deployment module's frozen-state probe.
def is_frozen() -> bool:
    return runtime_paths.is_frozen()
