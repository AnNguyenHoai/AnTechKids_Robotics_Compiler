"""Clean-machine launch contract for a packaged RoboStudio distribution.

The launcher uses an absolute application executable and the same artifact-
closed dependency environment used by production deployment/E2E. Development
Python, Node, PlatformIO and other global tools cannot leak through host PATH.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from tools import dependency_closure, runtime_preflight

LAUNCH_MANIFEST = "launch-manifest.json"
LAUNCH_SCHEMA = "antechkids.robostudio.clean-machine-launch"
LAUNCH_SCHEMA_VERSION = 1
DISTRIBUTION_MANIFEST = "distribution-manifest.json"


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
    try:
        return dependency_closure.assert_artifact_owned(
            executable, root, label="RoboStudio executable"
        )
    except dependency_closure.DependencyClosureError as exc:
        raise CleanMachineLaunchError(f"Packaged dependency closure failed: {exc}") from exc


def clean_machine_environment(root: Path, base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Build an artifact-closed environment for packaged RoboStudio."""
    try:
        env, _ = dependency_closure.build_closed_environment(root, base_env)
    except dependency_closure.DependencyClosureError as exc:
        raise CleanMachineLaunchError(f"Packaged dependency closure failed: {exc}") from exc
    return env


def build_launch_spec(
    root: Path,
    *,
    cwd: Path | None = None,
    args: Sequence[str] = (),
    base_env: Mapping[str, str] | None = None,
) -> LaunchSpec:
    """Create a deterministic packaged launch command."""
    root = Path(root).resolve()
    try:
        runtime_preflight.validate_distribution(root)
    except Exception as exc:
        raise CleanMachineLaunchError(f"Packaged runtime preflight failed: {exc}") from exc
    executable = _require_executable(root)
    launch_cwd = Path(cwd).resolve() if cwd is not None else root.parent
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
        "host_runtime_variables_removed": list(dependency_closure.HOST_INJECTION_VARS),
        "path_lookup_required": False,
        "path_policy": "artifact-closed-with-windows-system-allowlist",
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
    """Launch packaged RoboStudio without shell/host-PATH lookup."""
    spec = build_launch_spec(root, cwd=cwd, args=args, base_env=base_env)
    completed = subprocess.run(
        list(spec.command),
        cwd=str(spec.cwd),
        env=spec.environment,
        shell=False,
        check=False,
    )
    return completed.returncode
