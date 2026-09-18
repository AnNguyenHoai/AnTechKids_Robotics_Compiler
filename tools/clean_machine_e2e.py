"""Clean-machine end-to-end execution gate for RoboStudio.

RSD-01..RSD-12 prove that the portable runtime can be resolved, packaged,
relocated, and preflighted. This module closes the remaining execution gap by
actually starting the application-owned Python runtime in an unrelated working
directory with a hostile host environment.

The gate intentionally does not launch the GUI during automated tests. A GUI
process is long-lived and requires a display, while the portability property we
need to prove is at the process boundary: the packaged interpreter starts,
receives application-owned runtime paths, ignores host Python/PlatformIO state,
and keeps the caller's working directory external to the application.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from tools import dependency_closure, runtime_paths, runtime_preflight


class CleanMachineE2EError(RuntimeError):
    """Raised when the portable runtime cannot execute cleanly."""


@dataclass(frozen=True)
class CleanMachineE2EReport:
    application_root: Path
    python: Path
    cwd: Path
    returncode: int
    executable_verified: bool
    environment_verified: bool


def _canonical(path: Path) -> Path:
    """Return one canonical spelling for an existing filesystem path."""
    value = os.path.expanduser(str(path))
    return Path(os.path.normcase(os.path.realpath(os.path.abspath(value))))


def _python_path(root: Path) -> Path:
    relative = Path("runtime") / "bin" / ("python.exe" if os.name == "nt" else "python")
    return _canonical(root / relative)


def _clean_environment(root: Path, base_env: Mapping[str, str] | None) -> dict[str, str]:
    try:
        env, _ = dependency_closure.build_closed_environment(root, base_env)
    except dependency_closure.DependencyClosureError as exc:
        raise CleanMachineE2EError(f"Portable dependency closure failed: {exc}") from exc
    return env


_PROBE = r'''
import json, os, sys
from pathlib import Path
root = Path(os.environ["ROBOSTUDIO_HOME"]).resolve()
expected_python = root / "runtime" / "bin" / ("python.exe" if os.name == "nt" else "python")
expected_core = root / "runtime" / "platformio"
path_entries = [Path(value).resolve() for value in os.environ.get("PATH", "").split(os.pathsep) if value]
system_root = Path(os.environ.get("SystemRoot", os.environ.get("WINDIR", root))).resolve() if os.name == "nt" else None
allowed_system = ({system_root, system_root / "System32"} if system_root else set())
path_closed = all(path == root or root in path.parents or path in allowed_system for path in path_entries)
result = {
    "executable": str(Path(sys.executable).resolve()),
    "cwd": str(Path.cwd().resolve()),
    "application_home": os.environ.get("ROBOSTUDIO_HOME"),
    "runtime_mode": os.environ.get("ROBOSTUDIO_RUNTIME_MODE"),
    "dependency_mode": os.environ.get("ROBOSTUDIO_DEPENDENCY_MODE"),
    "core": os.environ.get("PLATFORMIO_CORE_DIR"),
    "platforms": os.environ.get("PLATFORMIO_PLATFORMS_DIR"),
    "packages": os.environ.get("PLATFORMIO_PACKAGES_DIR"),
    "host_pythonhome_present": "PYTHONHOME" in os.environ,
    "host_pythonpath_present": "PYTHONPATH" in os.environ,
    "host_virtualenv_present": "VIRTUAL_ENV" in os.environ,
    "host_nodepath_present": "NODE_PATH" in os.environ,
    "host_npm_prefix_present": "NPM_CONFIG_PREFIX" in os.environ or "npm_config_prefix" in os.environ,
    "host_piohome_present": "PIOHOME_DIR" in os.environ,
    "path_closed": path_closed,
    "executable_under_root": Path(sys.executable).resolve().is_relative_to(root),
    "executable_is_expected": Path(sys.executable).resolve() == expected_python,
    "core_is_expected": Path(os.environ["PLATFORMIO_CORE_DIR"]).resolve() == expected_core,
}
print(json.dumps(result, sort_keys=True))
if not (
    result["executable_under_root"]
    and result["executable_is_expected"]
    and result["core_is_expected"]
    and result["runtime_mode"] == "packaged"
    and result["dependency_mode"] == "artifact-closed"
    and result["path_closed"]
    and not result["host_pythonhome_present"]
    and not result["host_pythonpath_present"]
    and not result["host_virtualenv_present"]
    and not result["host_nodepath_present"]
    and not result["host_npm_prefix_present"]
    and not result["host_piohome_present"]
):
    raise SystemExit(3)
'''


def _validate_for_root(root: Path) -> None:
    previous = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)
    os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(root)
    try:
        runtime_preflight.validate_distribution(root)
    finally:
        if previous is None:
            os.environ.pop(runtime_paths.APPLICATION_HOME_ENV, None)
        else:
            os.environ[runtime_paths.APPLICATION_HOME_ENV] = previous


def execute_clean_machine_probe(root: Path, *, cwd: Path, base_env: Mapping[str, str] | None = None, timeout: float = 30.0) -> CleanMachineE2EReport:
    """Start the bundled Python process with an external CWD and closed env."""
    root = _canonical(Path(root))
    cwd = _canonical(Path(cwd))
    if not cwd.is_dir():
        raise CleanMachineE2EError(f"Clean-machine probe CWD does not exist: {cwd}")
    if root == cwd or root in cwd.parents:
        raise CleanMachineE2EError(f"Clean-machine probe CWD must be outside the application root: {cwd}")
    try:
        _validate_for_root(root)
    except Exception as exc:
        raise CleanMachineE2EError(f"Packaged runtime preflight failed: {exc}") from exc

    python = _python_path(root)
    if not python.is_file():
        raise CleanMachineE2EError(f"Portable Python is missing: {python}")
    try:
        dependency_closure.assert_artifact_owned(python, root, label="portable Python")
    except dependency_closure.DependencyClosureError as exc:
        raise CleanMachineE2EError(f"Portable dependency closure failed: {exc}") from exc
    env = _clean_environment(root, base_env)
    try:
        completed = subprocess.run([str(python), "-c", _PROBE], cwd=str(cwd), env=env, shell=False, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CleanMachineE2EError(f"Portable runtime execution failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no diagnostic output"
        raise CleanMachineE2EError(f"Portable runtime probe failed with exit code {completed.returncode}: {detail}")
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise CleanMachineE2EError(f"Portable runtime probe returned invalid diagnostics: {completed.stdout!r}") from exc

    observed_cwd = _canonical(Path(result["cwd"]))
    expected_python = _canonical(python)
    observed_python = _canonical(Path(result["executable"]))
    expected_core = _canonical(root / "runtime" / "platformio")
    environment_verified = (
        _canonical(Path(result["application_home"])) == root
        and result.get("runtime_mode") == "packaged"
        and result.get("dependency_mode") == "artifact-closed"
        and result.get("path_closed") is True
        and _canonical(Path(result["core"])) == expected_core
        and _canonical(Path(result["platforms"])) == _canonical(expected_core / "platforms")
        and _canonical(Path(result["packages"])) == _canonical(expected_core / "packages")
        and not result.get("host_pythonhome_present")
        and not result.get("host_pythonpath_present")
        and not result.get("host_virtualenv_present")
        and not result.get("host_nodepath_present")
        and not result.get("host_npm_prefix_present")
        and not result.get("host_piohome_present")
    )
    executable_verified = observed_python == expected_python and observed_python.is_relative_to(root)
    if observed_cwd != cwd:
        raise CleanMachineE2EError(f"Portable runtime changed its working directory: expected {cwd}, got {observed_cwd}")
    if observed_python != expected_python:
        raise CleanMachineE2EError(f"Portable runtime executable mismatch: expected {expected_python}, got {observed_python}")
    if not executable_verified:
        raise CleanMachineE2EError(f"Portable runtime escaped application root: expected {root}, got {observed_python}")
    if not environment_verified:
        raise CleanMachineE2EError("Portable runtime inherited or resolved a host-owned runtime environment")
    return CleanMachineE2EReport(root, python, cwd, completed.returncode, executable_verified, environment_verified)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate portable RoboStudio runtime execution")
    parser.add_argument("root", type=Path)
    parser.add_argument("--cwd", type=Path, required=True)
    args = parser.parse_args()
    report = execute_clean_machine_probe(args.root, cwd=args.cwd)
    print("RoboStudio clean-machine execution: PASS")
    print(f"Portable Python: {report.python}")
    print(f"External CWD: {report.cwd}")
