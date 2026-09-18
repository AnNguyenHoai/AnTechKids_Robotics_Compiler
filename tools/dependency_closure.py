"""Portable executable dependency/state-closure policy for RoboStudio.

Packaged execution is dependency-closed while its installation tree remains
immutable. Executables, PlatformIO platforms and packages resolve from the
artifact; mutable PlatformIO core service data, cache and build workspace live
under an external RoboStudio state root.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from tools import runtime_paths


class DependencyClosureError(RuntimeError):
    """Raised when packaged execution can escape to a host-owned dependency."""


MUTABLE_PLATFORMIO_VARS = (
    "PLATFORMIO_GLOBALLIB_DIR",
    "PLATFORMIO_CACHE_DIR",
    "PLATFORMIO_BUILD_CACHE_DIR",
    "PLATFORMIO_WORKSPACE_DIR",
    "PLATFORMIO_BUILD_DIR",
    "PLATFORMIO_LIBDEPS_DIR",
    "PLATFORMIO_SHARED_DIR",
)

HOST_INJECTION_VARS = (
    "PYTHONHOME",
    "PYTHONPATH",
    "VIRTUAL_ENV",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
    "NODE_PATH",
    "NPM_CONFIG_PREFIX",
    "npm_config_prefix",
    "PIOHOME_DIR",
    "PLATFORMIO_CORE_DIR",
    "PLATFORMIO_PLATFORMS_DIR",
    "PLATFORMIO_PACKAGES_DIR",
    *MUTABLE_PLATFORMIO_VARS,
)

_EXECUTABLE_SUFFIXES = {".exe", ".com", ".cmd", ".bat"}


@dataclass(frozen=True)
class DependencyClosureReport:
    application_root: Path
    state_root: Path
    path_entries: tuple[Path, ...]
    artifact_entries: tuple[Path, ...]
    system_entries: tuple[Path, ...]


def _canonical(path: Path | str) -> Path:
    value = os.path.expanduser(str(path))
    return Path(os.path.normcase(os.path.realpath(os.path.abspath(value))))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def assert_artifact_owned(path: Path | str, root: Path | str, *, label: str) -> Path:
    """Return a canonical path only when it is owned by the extracted artifact."""
    candidate = _canonical(path)
    artifact_root = _canonical(root)
    if candidate == artifact_root or _is_relative_to(candidate, artifact_root):
        return candidate
    raise DependencyClosureError(
        f"{label} resolved outside production artifact: {candidate} (root: {artifact_root})"
    )


def _contains_executable(directory: Path) -> bool:
    try:
        return any(
            child.is_file()
            and (
                child.suffix.lower() in _EXECUTABLE_SUFFIXES
                or (os.name != "nt" and os.access(child, os.X_OK))
            )
            for child in directory.iterdir()
        )
    except OSError:
        return False


def artifact_path_entries(root: Path | str) -> tuple[Path, ...]:
    """Discover only artifact-owned directories that can contain runtime tools."""
    root = _canonical(root)
    candidates: list[Path] = []
    for relative in (
        Path("."),
        Path("runtime") / "bin",
        Path("runtime") / "platformio" / "penv" / "Scripts",
    ):
        candidate = _canonical(root / relative)
        if candidate.is_dir() and (candidate == root or _is_relative_to(candidate, root)):
            candidates.append(candidate)

    runtime = root / "runtime"
    if runtime.is_dir():
        for directory in runtime.rglob("*"):
            if directory.is_dir() and _contains_executable(directory):
                candidate = _canonical(directory)
                if _is_relative_to(candidate, root):
                    candidates.append(candidate)

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = os.path.normcase(str(candidate))
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return tuple(unique)


def system_path_entries(base_env: Mapping[str, str] | None = None) -> tuple[Path, ...]:
    """Return the minimal OS-owned PATH allow-list required on Windows."""
    if os.name != "nt":
        return ()
    env = os.environ if base_env is None else base_env
    system_root_value = env.get("SystemRoot") or env.get("WINDIR")
    if not system_root_value:
        return ()
    system_root = _canonical(system_root_value)
    candidates = (system_root / "System32", system_root)
    return tuple(_canonical(path) for path in candidates if path.is_dir())


def _state_defaults(state_root: Path) -> dict[str, Path]:
    pio = state_root / "platformio"
    return {
        "PLATFORMIO_GLOBALLIB_DIR": pio / "lib",
        "PLATFORMIO_CACHE_DIR": pio / "cache",
        "PLATFORMIO_BUILD_CACHE_DIR": pio / "build-cache",
        "PLATFORMIO_WORKSPACE_DIR": pio / "workspace",
        "PLATFORMIO_BUILD_DIR": pio / "build",
        "PLATFORMIO_LIBDEPS_DIR": pio / "libdeps",
        "PLATFORMIO_SHARED_DIR": pio / "shared",
    }


def _trusted_mutable_path(value: str | None, state_root: Path) -> Path | None:
    """Accept caller state overrides only when they stay below our state root."""
    if not value:
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        return None
    candidate = _canonical(candidate)
    root = _canonical(state_root)
    if candidate == root or _is_relative_to(candidate, root):
        return candidate
    return None


def build_closed_environment(
    root: Path | str,
    base_env: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], DependencyClosureReport]:
    """Build a child environment with immutable dependencies + external state."""
    artifact_root = _canonical(root)
    if not artifact_root.is_dir():
        raise DependencyClosureError(f"production artifact root is missing: {artifact_root}")

    env = dict(os.environ if base_env is None else base_env)
    requested_mutable = {name: env.get(name) for name in MUTABLE_PLATFORMIO_VARS}
    try:
        state_root = runtime_paths.user_data_root(
            base_env=env,
            application_root_override=artifact_root,
            enforce_external=True,
        )
    except runtime_paths.RuntimePathError as exc:
        raise DependencyClosureError(f"invalid RoboStudio state root: {exc}") from exc

    for name in HOST_INJECTION_VARS:
        env.pop(name, None)

    artifact_entries = artifact_path_entries(artifact_root)
    system_entries = system_path_entries(env)
    path_entries = artifact_entries + system_entries
    env["PATH"] = os.pathsep.join(str(entry) for entry in path_entries)
    env["ROBOSTUDIO_HOME"] = str(artifact_root)
    env["ROBOSTUDIO_STATE_ROOT"] = str(state_root)
    env["ROBOSTUDIO_RUNTIME_MODE"] = "packaged"
    env["ROBOSTUDIO_DEPENDENCY_MODE"] = "artifact-closed"

    packaged_platformio = artifact_root / "runtime" / "platformio"
    mutable_platformio = state_root / "platformio"
    # PlatformIO core_dir contains mutable service data. Keep only immutable
    # dependency stores (platforms/packages) inside the production artifact.
    env["PLATFORMIO_CORE_DIR"] = str(mutable_platformio / "core")
    env["PLATFORMIO_PLATFORMS_DIR"] = str(packaged_platformio / "platforms")
    env["PLATFORMIO_PACKAGES_DIR"] = str(packaged_platformio / "packages")

    defaults = _state_defaults(state_root)
    for name, default in defaults.items():
        trusted = _trusted_mutable_path(requested_mutable.get(name), state_root)
        env[name] = str(trusted or default)

    env["PLATFORMIO_DISABLE_UPGRADE_CHECK"] = "true"
    env["PLATFORMIO_DISABLE_PROGRESSBAR"] = "true"
    env["PLATFORMIO_NO_ANSI"] = "true"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    report = DependencyClosureReport(
        application_root=artifact_root,
        state_root=state_root,
        path_entries=path_entries,
        artifact_entries=artifact_entries,
        system_entries=system_entries,
    )
    validate_closed_environment(report)
    return env, report


def validate_closed_environment(report: DependencyClosureReport) -> None:
    """Reject PATH/state overlap with the immutable production artifact."""
    root = _canonical(report.application_root)
    state = _canonical(report.state_root)
    if state == root or _is_relative_to(state, root):
        raise DependencyClosureError(
            f"mutable state overlaps production artifact: {state} (root: {root})"
        )
    allowed_system = {_canonical(path) for path in report.system_entries}
    for entry in report.path_entries:
        candidate = _canonical(entry)
        if candidate == root or _is_relative_to(candidate, root):
            continue
        if candidate in allowed_system:
            continue
        raise DependencyClosureError(f"host-owned PATH entry escaped dependency closure: {candidate}")


def resolve_artifact_executable(
    name: str,
    *,
    root: Path | str,
    environment: Mapping[str, str],
) -> Path:
    """Resolve a required executable and require the result to live in the artifact."""
    if not name or Path(name).name != name:
        raise DependencyClosureError(f"executable name must be a basename: {name!r}")
    resolved = shutil.which(name, path=environment.get("PATH", ""))
    if not resolved:
        raise DependencyClosureError(
            f"required artifact dependency is missing: {name}; host PATH fallback is disabled"
        )
    return assert_artifact_owned(resolved, root, label=f"required dependency {name}")


def validate_artifact_command(
    command: Sequence[str],
    *,
    root: Path | str,
    environment: Mapping[str, str],
    label: str,
) -> Path:
    """Require a top-level production command to start from an artifact-owned binary."""
    if not command:
        raise DependencyClosureError(f"{label} command is empty")
    token = command[0].strip('"')
    candidate = Path(token)
    is_path = candidate.is_absolute() or candidate.parent != Path(".")
    if is_path:
        if not candidate.is_file():
            raise DependencyClosureError(f"{label} executable is missing: {candidate}")
        return assert_artifact_owned(candidate, root, label=f"{label} executable")

    resolved = shutil.which(token, path=environment.get("PATH", ""))
    if not resolved:
        raise DependencyClosureError(
            f"{label} executable is missing from production artifact: {token}; host PATH fallback is disabled"
        )
    return assert_artifact_owned(resolved, root, label=f"{label} executable")


def path_evidence(report: DependencyClosureReport) -> dict[str, object]:
    root = _canonical(report.application_root)

    def relative_or_absolute(path: Path) -> str:
        candidate = _canonical(path)
        if candidate == root:
            return "."
        if _is_relative_to(candidate, root):
            return candidate.relative_to(root).as_posix()
        return str(candidate)

    return {
        "mode": "artifact-closed",
        "artifact_path_entries": [relative_or_absolute(path) for path in report.artifact_entries],
        "system_path_entries": [str(path) for path in report.system_entries],
        "host_path_inherited": False,
        "state_root": str(report.state_root),
        "state_outside_artifact": True,
    }
