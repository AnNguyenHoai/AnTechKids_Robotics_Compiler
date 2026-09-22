"""Runtime helpers for reliable RoboStudio deployment subprocesses.

The deployment boundary must not depend on a shell command being available on
PATH and must not leave a GUI operation blocked forever. This module provides a
small, UI-independent process runner with bounded execution and line-oriented
output streaming, plus an application-owned PlatformIO runtime environment.
"""
from __future__ import annotations

import hashlib
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
DEPENDENCY_MODE_ENV = "ROBOSTUDIO_DEPENDENCY_MODE"
DEPENDENCY_MODE_CLOSED = "artifact-closed"
PLATFORMIO_DEPENDENCY_ALIAS_ROOT_ENV = "ROBOSTUDIO_PLATFORMIO_DEPENDENCY_ALIAS_ROOT"
WINDOWS_SHORT_ALIAS_DIRECTORY = "RSC"
WINDOWS_MAX_SAFE_ALIAS_BASE_LENGTH = 80


class DeploymentRuntimeError(RuntimeError):
    """Raised when a deployment subprocess cannot be started or times out."""


@dataclass(frozen=True)
class ProcessResult:
    """Completed process information plus the complete combined output."""

    returncode: int
    output: str


def is_frozen() -> bool:
    """Return whether RoboStudio is executing as a packaged application."""
    return runtime_paths.is_frozen()


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
    """Return the immutable PlatformIO/deployment dependency payload root."""
    return application_root() / "runtime" / "platformio"


def deployment_runtime_core_dir() -> Path:
    """Return the writable PlatformIO Core service-data directory.

    B2.3 separates immutable platforms/packages from mutable PlatformIO Core
    state. Callers that need the bundled payload must use
    :func:`deployment_runtime_root`; Core state always belongs under the
    external RoboStudio state root.
    """
    state = runtime_paths.user_data_root(
        application_root_override=application_root(),
        enforce_external=_dependency_closed_mode(),
    )
    return state / "platformio" / "core"


def _dependency_closed_mode(base_env: Mapping[str, str] | None = None) -> bool:
    """Return whether this process belongs to the packaged dependency boundary.

    A portable Python helper launched by frozen RoboStudio is not itself a
    PyInstaller/frozen process. The explicit dependency-mode marker therefore
    propagates production closure to nested compiler/PlatformIO/flash children.
    """
    environment = os.environ if base_env is None else base_env
    return is_frozen() or environment.get(DEPENDENCY_MODE_ENV) == DEPENDENCY_MODE_CLOSED


def _same_directory(left: Path, right: Path) -> bool:
    try:
        return os.path.samefile(left, right)
    except (OSError, ValueError):
        return False


def _windows_cmd(environment: Mapping[str, str]) -> Path:
    system_root = environment.get("SystemRoot") or environment.get("WINDIR")
    if not system_root:
        raise DeploymentRuntimeError(
            "Windows SystemRoot is unavailable; cannot create the short PlatformIO dependency alias."
        )
    command = Path(system_root) / "System32" / "cmd.exe"
    if not command.is_file():
        raise DeploymentRuntimeError(
            f"Windows command processor is unavailable for PlatformIO dependency aliasing: {command}"
        )
    return command


def _windows_alias_base_is_safe(path: Path) -> bool:
    text = str(path)
    return (
        path.is_absolute()
        and len(text) <= WINDOWS_MAX_SAFE_ALIAS_BASE_LENGTH
        and not any(char.isspace() for char in text)
    )


def _windows_dependency_alias_base(
    state: Path,
    environment: Mapping[str, str],
) -> Path:
    """Select a short whitespace-free base for PlatformIO dependency junctions.

    Keep aliases under RoboStudio state when that path is already safe. If a
    Windows account/profile contains whitespace (for example ``EASTVN - An
    Nguyen``) or is too long for the legacy Xtensa toolchain, fall back to the
    Public profile. Failing closed is safer than silently recreating the same
    broken include/tool path on the target PC.
    """
    state_candidate = Path(state).expanduser().resolve() / "p"
    if _windows_alias_base_is_safe(state_candidate):
        try:
            state_candidate.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DeploymentRuntimeError(
                f"Unable to create PlatformIO dependency alias root {state_candidate}: {exc}"
            ) from exc
        return state_candidate

    public_value = str(environment.get("PUBLIC", "")).strip()
    if not public_value:
        raise DeploymentRuntimeError(
            "Windows PUBLIC profile is unavailable and RoboStudio state is not a short "
            "whitespace-free path for ESP32 PlatformIO dependencies."
        )
    public_candidate = Path(public_value).expanduser().resolve() / WINDOWS_SHORT_ALIAS_DIRECTORY
    if not _windows_alias_base_is_safe(public_candidate):
        raise DeploymentRuntimeError(
            "Windows PUBLIC profile is not a short whitespace-free PlatformIO alias root: "
            f"{public_candidate}"
        )
    try:
        public_candidate.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DeploymentRuntimeError(
            f"Unable to create Windows PlatformIO short-path root {public_candidate}: {exc}"
        ) from exc
    return public_candidate


def _ensure_windows_junction(
    alias: Path,
    target: Path,
    environment: Mapping[str, str],
) -> Path:
    """Create one external directory junction without copying immutable payload.

    Espressif's legacy Windows Xtensa GCC driver can fail to spawn ``cc1plus`` or
    resolve Arduino variant headers when the PlatformIO package path is long or
    contains whitespace. The release itself may live in an arbitrarily named
    directory, and the Windows user profile may also contain spaces, so packaged
    execution exposes immutable platform/package stores through a short external
    junction. The junction is only an alias: package bytes remain application-
    owned and are never copied or edited.
    """
    target = target.resolve()
    if not target.is_dir():
        raise DeploymentRuntimeError(f"Bundled PlatformIO dependency directory is missing: {target}")
    alias.parent.mkdir(parents=True, exist_ok=True)

    if os.path.lexists(alias):
        if _same_directory(alias, target):
            return alias
        raise DeploymentRuntimeError(
            f"PlatformIO short-path alias already exists with a different target: {alias}"
        )

    command = _windows_cmd(environment)
    result = subprocess.run(
        [str(command), "/d", "/c", "mklink", "/J", str(alias), str(target)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=15.0,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0 or not _same_directory(alias, target):
        detail = result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise DeploymentRuntimeError(
            f"Unable to create short PlatformIO dependency alias {alias} -> {target}{suffix}"
        )
    return alias


def prepare_platformio_dependency_aliases(
    root: Path,
    environment: Mapping[str, str],
) -> dict[str, str]:
    """Return a packaged environment with Windows-safe short dependency paths.

    On non-Windows systems the canonical artifact paths are returned unchanged.
    On Windows, ``platforms`` and ``packages`` are exposed through external
    directory junctions. If the RoboStudio state path is already short and has
    no whitespace it is used directly. Otherwise a short Public-profile root is
    selected so usernames containing spaces cannot leak into GCC include/tool
    paths. ``Path.resolve``/``samefile`` still resolves aliases to the immutable
    artifact, preserving dependency ownership.
    """
    env = dict(environment)
    if os.name != "nt":
        return env

    artifact_root = Path(root).expanduser().resolve()
    platforms = artifact_root / "runtime" / "platformio" / "platforms"
    packages = artifact_root / "runtime" / "platformio" / "packages"
    try:
        dependency_closure.assert_artifact_owned(
            platforms, artifact_root, label="PlatformIO platforms"
        )
        dependency_closure.assert_artifact_owned(
            packages, artifact_root, label="PlatformIO packages"
        )
        state = runtime_paths.prepare_user_data_root(
            base_env=env,
            application_root_override=artifact_root,
            enforce_external=True,
        )
        alias_base = _windows_dependency_alias_base(state, env)
    except (dependency_closure.DependencyClosureError, runtime_paths.RuntimePathError) as exc:
        raise DeploymentRuntimeError(f"Unable to prepare PlatformIO dependency aliases: {exc}") from exc

    identity = hashlib.sha256(str(artifact_root).casefold().encode("utf-8")).hexdigest()[:8]
    alias_root = alias_base / identity
    platform_alias = _ensure_windows_junction(alias_root / "f", platforms, env)
    package_alias = _ensure_windows_junction(alias_root / "k", packages, env)

    env[PLATFORMIO_PLATFORMS_DIR_ENV] = str(platform_alias)
    env[PLATFORMIO_PACKAGES_DIR_ENV] = str(package_alias)
    env[PLATFORMIO_DEPENDENCY_ALIAS_ROOT_ENV] = str(alias_root)

    # Prefer short tool-package bin directories during child-process/DLL lookup.
    # Package identity still resolves through the junction to the artifact.
    package_bins = [
        child / "bin"
        for child in package_alias.iterdir()
        if child.is_dir() and (child / "bin").is_dir()
    ]
    if package_bins:
        existing = env.get("PATH", "")
        env["PATH"] = os.pathsep.join(
            [*(str(path) for path in package_bins), *([existing] if existing else [])]
        )
    return env


def deployment_runtime_environment(
    base_env: Mapping[str, str] | None = None,
    *,
    project_name: str | None = None,
) -> dict[str, str]:
    """Build the environment for a deployment subprocess.

    Packaged RoboStudio and its portable-Python descendants are dependency-
    closed: executable lookup is limited to application-owned directories plus
    the minimal Windows system allow-list, and host Python/Node/PlatformIO
    injection variables are removed. This prevents a packaged deployment from
    passing only because development tools happen to exist on the machine.

    Source builds intentionally retain their developer environment. When
    ``project_name`` is supplied, writable build state is still moved to the
    per-project RoboStudio user-data workspace.
    """
    if _dependency_closed_mode(base_env):
        try:
            env, _ = dependency_closure.build_closed_environment(application_root(), base_env)
        except dependency_closure.DependencyClosureError as exc:
            raise DeploymentRuntimeError(f"Packaged dependency closure failed: {exc}") from exc
        env = prepare_platformio_dependency_aliases(application_root(), env)
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
    """Validate the complete packaged ESP32 firmware deployment runtime."""
    root = deployment_runtime_root()
    if not root.is_dir():
        raise DeploymentRuntimeError(f"RoboStudio deployment runtime is missing: {root}")
    if not (root / "platforms").is_dir():
        raise DeploymentRuntimeError(
            f"RoboStudio deployment runtime is missing platforms: {root / 'platforms'}"
        )
    packages = root / "packages"
    if not packages.is_dir():
        raise DeploymentRuntimeError(
            f"RoboStudio deployment runtime is missing packages: {packages}"
        )
    _validate_esp32_runtime_payload(packages)
    return root


def python_command(*args: str) -> list[str]:
    """Build a Python command that is portable in frozen RoboStudio.

    ``sys.executable`` is the RoboStudio executable in a frozen/PyInstaller
    build, not a general Python interpreter. Deployment helper scripts must
    therefore resolve the application-owned interpreter explicitly.
    """
    try:
        return runtime_paths.python_command(*args)
    except runtime_paths.RuntimePathError as exc:
        raise DeploymentRuntimeError(f"Packaged Python runtime is unavailable: {exc}") from exc


def platformio_command(*args: str) -> list[str]:
    """Build the PlatformIO command through the RoboStudio runtime resolver."""
    return resolve_platformio_command(*args)


def _prepare_process_environment(
    command: Sequence[str],
    env: Mapping[str, str] | None,
) -> Mapping[str, str] | None:
    """Seal production subprocesses at the process-launch boundary.

    Callers are allowed to add application values such as Wi-Fi credentials,
    but packaged RoboStudio or a portable-Python descendant may not re-open
    host PATH/PYTHONPATH by passing ``os.environ.copy()`` or by omitting
    ``env``. The runner therefore applies B2.2 dependency closure immediately
    before ``Popen`` and validates that the executable belongs to the artifact.

    Source/development runs intentionally preserve their historical behavior.
    """
    if not _dependency_closed_mode(env):
        return dict(env) if env is not None else None

    closed = deployment_runtime_environment(env)
    try:
        dependency_closure.validate_artifact_command(
            list(command),
            root=application_root(),
            environment=closed,
            label="deployment command",
        )
    except dependency_closure.DependencyClosureError as exc:
        raise DeploymentRuntimeError(f"Packaged deployment command rejected: {exc}") from exc
    return closed


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

    Production launches are sealed here, at the final subprocess boundary.
    Closure propagates from frozen RoboStudio into portable Python helpers via
    ``ROBOSTUDIO_DEPENDENCY_MODE=artifact-closed``, so nested PlatformIO/flash
    processes cannot accidentally regain the host environment.

    The child is isolated into a process group so a timeout does not leave a
    compiler/PlatformIO descendant running after RoboStudio reports failure.
    Output is retained even for non-zero exits, allowing callers to surface a
    useful diagnostic without coupling the runner to any UI toolkit.
    """
    if not command:
        raise ValueError("Deployment command must not be empty.")
    if timeout <= 0:
        raise ValueError("Deployment process timeout must be greater than zero.")

    process_env = _prepare_process_environment(command, env)
    popen_kwargs: dict[str, object] = {
        "cwd": str(Path(cwd)),
        "env": process_env,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "bufsize": 1,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        popen_kwargs["start_new_session"] = True

    try:
        process = subprocess.Popen(list(command), **popen_kwargs)
    except OSError as exc:
        raise DeploymentRuntimeError(
            f"Unable to start deployment command {command[0]!r}: {exc}"
        ) from exc

    output_parts: list[str] = []
    reader_error: list[BaseException] = []

    def _read_output() -> None:
        assert process.stdout is not None
        try:
            for line in iter(process.stdout.readline, ""):
                output_parts.append(line)
                if on_output is not None:
                    on_output(line)
        except BaseException as exc:  # pragma: no cover - defensive reader boundary
            reader_error.append(exc)
        finally:
            try:
                process.stdout.close()
            except OSError:
                pass

    reader = threading.Thread(
        target=_read_output,
        name="robostudio-deployment-output",
        daemon=True,
    )
    reader.start()
    started = time.monotonic()
    timed_out = False
    while process.poll() is None:
        if time.monotonic() - started >= timeout:
            timed_out = True
            _terminate_process_tree(process)
            break
        time.sleep(0.05)

    if timed_out and process.poll() is None:
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            _kill_process_tree(process)

    try:
        returncode = process.wait(timeout=5.0)
    except subprocess.TimeoutExpired as exc:
        _kill_process_tree(process)
        raise DeploymentRuntimeError("Deployment process could not be terminated cleanly") from exc
    reader.join(timeout=2.0)

    output = "".join(output_parts)
    if reader_error:
        raise DeploymentRuntimeError(f"Unable to read deployment output: {reader_error[0]}")
    if timed_out:
        detail = output.strip()
        suffix = f"\n{detail}" if detail else ""
        raise DeploymentRuntimeError(
            f"Deployment process timed out after {timeout:g} seconds.{suffix}"
        )
    return ProcessResult(returncode=returncode, output=output)
