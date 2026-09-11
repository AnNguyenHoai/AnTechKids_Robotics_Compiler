"""Clean-machine launch contract for a packaged RoboStudio distribution.

RSD-07 proves that a distribution can be assembled. RSD-08 proves that the
assembled artifact can be launched without inheriting a developer machine's
Python/PlatformIO configuration. The launcher uses an absolute application
executable and prepares only application-owned runtime variables; it never
needs the repository checkout or a PlatformIO installation on PATH.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from tools import runtime_preflight, runtime_paths

LAUNCH_MANIFEST = "launch-manifest.json"
LAUNCH_SCHEMA = "antechkids.robostudio.clean-machine-launch"
LAUNCH_SCHEMA_VERSION = 1
DISTRIBUTION_MANIFEST = "distribution-manifest.json"

_HOST_RUNTIME_VARS = (
    "PYTHONHOME",
    "PYTHONPATH",
    "VIRTUAL_ENV",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
    "PIOHOME_DIR",
    "PLATFORMIO_CORE_DIR",
    "PLATFORMIO_PLATFORMS_DIR",
    "PLATFORMIO_PACKAGES_DIR",
    "PLATFORMIO_CACHE_DIR",
    "PLATFORMIO_BUILD_CACHE_DIR",
    "PLATFORMIO_WORKSPACE_DIR",
)


class CleanMachineLaunchError(RuntimeError):
    """Raised when a distribution cannot satisfy the clean-machine contract."""


@dataclass(frozen=True)
class LaunchSpec:
    """Absolute command, external working directory, and child environment."""

    executable: Path
    command: tuple[str, ...]
    cwd: Path
    environment: dict[str, str]


def _require_executable(root: Path) -> Path:
    manifest = root / DISTRIBUTION_MANIFEST
    if not manifest.is_file():
        raise CleanMachineLaunchError(f"Missing distribution manifest: {manifest}")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CleanMachineLaunchError(f"Unable to load distribution manifest: {exc}") from exc
    name = data.get("application")
    if not isinstance(name, str) or not name:
        raise CleanMachineLaunchError("Distribution manifest does not declare an application executable")
    executable = root / name
    if not executable.is_file():
        raise CleanMachineLaunchError(f"RoboStudio executable is missing: {executable}")
    return executable


def clean_machine_environment(root: Path, base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Build a host-independent environment for a packaged RoboStudio child."""
    root = Path(root)
    source = dict(os.environ if base_env is None else base_env)
    for name in _HOST_RUNTIME_VARS:
        source.pop(name, None)
    core = root / "runtime" / "platformio"
    source[runtime_paths.APPLICATION_HOME_ENV] = str(root)
    source["ROBOSTUDIO_RUNTIME_MODE"] = "packaged"
    source["PLATFORMIO_CORE_DIR"] = str(core)
    source["PLATFORMIO_PLATFORMS_DIR"] = str(core / "platforms")
    source["PLATFORMIO_PACKAGES_DIR"] = str(core / "packages")
    source["PLATFORMIO_CACHE_DIR"] = str(core / ".cache")
    source["PLATFORMIO_BUILD_CACHE_DIR"] = str(core / "build-cache")
    source["PLATFORMIO_WORKSPACE_DIR"] = str(core / "workspace")
    source["PLATFORMIO_DISABLE_UPGRADE_CHECK"] = "true"
    source["PLATFORMIO_DISABLE_PROGRESSBAR"] = "true"
    source["PLATFORMIO_NO_ANSI"] = "true"
    source["PYTHONIOENCODING"] = "utf-8"
    return source


def build_launch_spec(
    root: Path,
    *,
    cwd: Path | None = None,
    args: Sequence[str] = (),
    base_env: Mapping[str, str] | None = None,
) -> LaunchSpec:
    """Create a deterministic packaged launch command."""
    root = Path(root)
    try:
        runtime_preflight.validate_distribution(root)
    except Exception as exc:
        raise CleanMachineLaunchError(f"Packaged runtime preflight failed: {exc}") from exc
    executable = _require_executable(root)
    launch_cwd = Path(cwd) if cwd is not None else root.parent
    return LaunchSpec(
        executable=executable,
        command=(str(executable), *tuple(args)),
        cwd=launch_cwd,
        environment=clean_machine_environment(root, base_env),
    )


def write_launch_manifest(root: Path) -> Path:
    """Write a machine-readable record of the clean-machine launch contract."""
    root = Path(root)
    spec = build_launch_spec(root)
    manifest = {
        "schema": LAUNCH_SCHEMA,
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "application": spec.executable.name,
        "command_is_absolute": True,
        "cwd_must_be_external": True,
        "host_runtime_variables_removed": list(_HOST_RUNTIME_VARS),
        "path_lookup_required": False,
        "platformio_core": "runtime/platformio",
    }
    path = root / LAUNCH_MANIFEST
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def launch(
    root: Path,
    *,
    args: Sequence[str] = (),
    cwd: Path | None = None,
    base_env: Mapping[str, str] | None = None,
) -> int:
    """Launch packaged RoboStudio without shell/PATH lookup."""
    spec = build_launch_spec(root, cwd=cwd, args=args, base_env=base_env)
    completed = subprocess.run(
        list(spec.command),
        cwd=str(spec.cwd),
        env=spec.environment,
        shell=False,
        check=False,
    )
    return completed.returncode
