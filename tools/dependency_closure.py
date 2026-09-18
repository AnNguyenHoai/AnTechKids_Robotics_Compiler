"""Portable executable dependency-closure policy for RoboStudio.

B2.2 requires packaged execution to be deterministic on a clean Windows host:
application dependencies may be resolved only from the extracted artifact.  A
small Windows system allow-list remains on PATH for OS-owned process helpers;
user/global development-tool directories are deliberately excluded.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class DependencyClosureError(RuntimeError):
    """Raised when packaged execution can escape to a host-owned dependency."""


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
    "PLATFORMIO_CACHE_DIR",
    "PLATFORMIO_BUILD_CACHE_DIR",
    "PLATFORMIO_WORKSPACE_DIR",
)

_EXECUTABLE_SUFFIXES = {".exe", ".com", ".cmd", ".bat"}


@dataclass(frozen=True)
class DependencyClosureReport:
    application_root: Path
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

    # Stable layout entries are kept even when currently empty so that a tool
    # materialised by a later packaging step still resolves from the artifact.
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


def build_closed_environment(
    root: Path | str,
    base_env: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], DependencyClosureReport]:
    """Build a child environment whose executable PATH is artifact-closed."""
    artifact_root = _canonical(root)
    if not artifact_root.is_dir():
        raise DependencyClosureError(f"production artifact root is missing: {artifact_root}")

    env = dict(os.environ if base_env is None else base_env)
    for name in HOST_INJECTION_VARS:
        env.pop(name, None)

    artifact_entries = artifact_path_entries(artifact_root)
    system_entries = system_path_entries(env)
    path_entries = artifact_entries + system_entries
    env["PATH"] = os.pathsep.join(str(entry) for entry in path_entries)
    env["ROBOSTUDIO_DEPENDENCY_MODE"] = "artifact-closed"

    report = DependencyClosureReport(
        application_root=artifact_root,
        path_entries=path_entries,
        artifact_entries=artifact_entries,
        system_entries=system_entries,
    )
    validate_closed_environment(report)
    return env, report


def validate_closed_environment(report: DependencyClosureReport) -> None:
    """Reject any PATH entry that is neither artifact-owned nor OS-allowlisted."""
    root = _canonical(report.application_root)
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
    }
