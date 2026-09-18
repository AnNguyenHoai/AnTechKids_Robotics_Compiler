"""Runtime helpers for reliable RoboStudio deployment subprocesses.

The deployment boundary must not depend on a shell command being available on
PATH and must not leave a GUI operation blocked forever. This module provides a
small, UI-independent process runner with bounded execution and line-oriented
output streaming, plus an application-owned PlatformIO runtime environment.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from tools import build_isolation, dependency_closure, runtime_paths
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
    """Resolve the deployment application root deterministically.

    An explicit ``ROBOSTUDIO_HOME`` override is intentionally preserved as
    supplied (apart from ``~`` expansion). This keeps the deployment runtime
    contract identical to the application-owned path supplied by the caller;
    filesystem canonicalization belongs to resource APIs that explicitly need
    it, not to the identity of the packaged root.
    """
    override = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)
    if override:
        return Path(override).expanduser()
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return runtime_paths.application_root()


def deployment_runtime_root() -> Path:
    """Return the immutable PlatformIO/deployment runtime root."""
    return application_root() / "runtime" / "platformio"


def deployment_runtime_core_dir() -> Path:
    """Return the private PlatformIO Core data directory shipped by RoboStudio."""
    return deployment_runtime_root()


def deployment_runtime_environment(
    base_env: Mapping[str, str] | None = None,
    *,
    project_name: str | None = None,
) -> dict[str, str]:
    """Build the environment for a deployment subprocess.

    Frozen RoboStudio is dependency-closed: executable lookup is limited to
    application-owned directories plus the minimal Windows system allow-list,
    and host Python/Node/PlatformIO injection variables are removed. This
    prevents a packaged deployment from passing only because development tools
    happen to exist on the machine running RoboStudio.

    Source builds intentionally retain their developer environment. When
    ``project_name`` is supplied, writable build state is still moved to the
    per-project RoboStudio user-data workspace.
    """
    if is_frozen():
        try:
            env, _ = dependency_closure.build_closed_environment(application_root(), base_env)
        except dependency_closure.DependencyClosureError as exc:
            raise DeploymentRuntimeError(f"Packaged dependency closure failed: {exc}") from exc
    else:
        env = dict(os.environ if base_env is None else base_env)

    if project_name is not None:
        env = build_isolation.build_environment(project_name, env)

    return env


def isolated_deployment_environment(
    project_name: str,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return the canonical deployment environment with isolated build state."""
    return deployment_runtime_environment(base_env, project_name=project_name)


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


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """Terminate a deployment process and any children it owns.

    The deployment process is placed in its own process group on supported
    platforms. On POSIX, the group can therefore be terminated directly. On
    Windows, ``taskkill /T`` is used as a best-effort process-tree fallback;
    this is deliberately invoked without a shell. B2.2 keeps ``System32`` in
    the packaged PATH allow-list so this OS-owned helper remains available.
    """
    if process.poll() is not None:
        return

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5.0,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return
        except (OSError, subprocess.SubprocessError):
            pass

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except (AttributeError, OSError, ProcessLookupError):
        try:
            process.terminate()
        except OSError:
            pass


def _kill_process_tree(process: subprocess.Popen[str]) -> None:
    """Force-kill a deployment process group after graceful termination fails."""
    if process.poll() is not None:
        return

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5.0,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return
        except (OSError, subprocess.SubprocessError):
            pass

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (AttributeError, OSError, ProcessLookupError):
        try:
            process.kill()
        except OSError:
            pass


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_PROCESS_TIMEOUT_SECONDS,
    on_output: Callable[[str], None] | None = None,
) -> ProcessResult:
    """Run a process, stream combined output, and enforce a hard deadline.

    The child is isolated into a process group so a timeout does not leave a
    compiler/PlatformIO descendant running after RoboStudio reports failure.
    Output is retained even for non-zero exits, allowing callers to surface a
    useful diagnostic without coupling the runner to any UI toolkit.
    """
    if not command:
        raise ValueError("Deployment command must not be empty.")
    if timeout <= 0:
        raise ValueError("Deployment process timeout must be greater than zero.")

    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        start_new_session = True

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
            creationflags=creationflags,
            start_new_session=start_new_session,
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
            _terminate_process_tree(process)
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                _kill_process_tree(process)
                process.wait(timeout=5.0)
            reader_done.wait(timeout=2.0)
            raise DeploymentRuntimeError(
                f"Deployment command timed out after {timeout:.0f}s. "
                f"Output: {''.join(output).strip()}"
            )
        time.sleep(0.05)

    reader_done.wait(timeout=2.0)
    return ProcessResult(process.returncode, "".join(output))


# Keep this local alias for compatibility with existing tests that patch the
# deployment module's frozen-state probe.
def is_frozen() -> bool:
    return runtime_paths.is_frozen()
