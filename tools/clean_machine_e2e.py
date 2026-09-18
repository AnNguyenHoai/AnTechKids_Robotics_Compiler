"""Clean-machine end-to-end execution gate for RoboStudio.

The probe actually starts the application-owned Python runtime from an unrelated
working directory with a hostile host environment. It proves both B2.2
dependency closure and B2.3 mutable-state isolation: executable dependencies,
PlatformIO platforms and packages stay in the artifact; PlatformIO core/cache
state stays below an external RoboStudio state root.
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


def _canonical(path: Path | str) -> Path:
    value = os.path.expanduser(str(path))
    return Path(os.path.normcase(os.path.realpath(os.path.abspath(value))))


def _inside(path: Path | str, root: Path | str) -> bool:
    candidate = _canonical(path)
    parent = _canonical(root)
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def _python_path(root: Path) -> Path:
    relative = Path("runtime") / "bin" / ("python.exe" if os.name == "nt" else "python")
    return _canonical(root / relative)


def _clean_environment(
    root: Path, base_env: Mapping[str, str] | None
) -> dict[str, str]:
    try:
        env, _ = dependency_closure.build_closed_environment(root, base_env)
    except dependency_closure.DependencyClosureError as exc:
        raise CleanMachineE2EError(
            f"Portable dependency closure failed: {exc}"
        ) from exc
    return env


_PROBE = r'''
import json, os, sys
from pathlib import Path
root = Path(os.environ["ROBOSTUDIO_HOME"]).resolve()
state = Path(os.environ["ROBOSTUDIO_STATE_ROOT"]).resolve()
expected_python = root / "runtime" / "bin" / ("python.exe" if os.name == "nt" else "python")
expected_payload = root / "runtime" / "platformio"
core = Path(os.environ["PLATFORMIO_CORE_DIR"]).resolve()
platforms = Path(os.environ["PLATFORMIO_PLATFORMS_DIR"]).resolve()
packages = Path(os.environ["PLATFORMIO_PACKAGES_DIR"]).resolve()
cache = Path(os.environ["PLATFORMIO_CACHE_DIR"]).resolve()
path_entries = [Path(value).resolve() for value in os.environ.get("PATH", "").split(os.pathsep) if value]
system_root = Path(os.environ.get("SystemRoot", os.environ.get("WINDIR", root))).resolve() if os.name == "nt" else None
allowed_system = ({system_root, system_root / "System32"} if system_root else set())
path_closed = all(path == root or root in path.parents or path in allowed_system for path in path_entries)

def inside(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False

result = {
    "executable": str(Path(sys.executable).resolve()),
    "cwd": str(Path.cwd().resolve()),
    "application_home": os.environ.get("ROBOSTUDIO_HOME"),
    "state_root": str(state),
    "runtime_mode": os.environ.get("ROBOSTUDIO_RUNTIME_MODE"),
    "dependency_mode": os.environ.get("ROBOSTUDIO_DEPENDENCY_MODE"),
    "core": str(core),
    "platforms": str(platforms),
    "packages": str(packages),
    "cache": str(cache),
    "host_pythonhome_present": "PYTHONHOME" in os.environ,
    "host_pythonpath_present": "PYTHONPATH" in os.environ,
    "host_virtualenv_present": "VIRTUAL_ENV" in os.environ,
    "host_nodepath_present": "NODE_PATH" in os.environ,
    "host_npm_prefix_present": "NPM_CONFIG_PREFIX" in os.environ or "npm_config_prefix" in os.environ,
    "host_piohome_present": "PIOHOME_DIR" in os.environ,
    "path_closed": path_closed,
    "executable_under_root": inside(Path(sys.executable).resolve(), root),
    "executable_is_expected": Path(sys.executable).resolve() == expected_python,
    "state_outside_root": not inside(state, root),
    "core_under_state": inside(core, state),
    "core_outside_root": not inside(core, root),
    "cache_under_state": inside(cache, state),
    "cache_outside_root": not inside(cache, root),
    "platforms_are_bundled": platforms == expected_payload / "platforms",
    "packages_are_bundled": packages == expected_payload / "packages",
}
print(json.dumps(result, sort_keys=True))
if not (
    result["executable_under_root"]
    and result["executable_is_expected"]
    and result["state_outside_root"]
    and result["core_under_state"]
    and result["core_outside_root"]
    and result["cache_under_state"]
    and result["cache_outside_root"]
    and result["platforms_are_bundled"]
    and result["packages_are_bundled"]
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


def execute_clean_machine_probe(
    root: Path,
    *,
    cwd: Path,
    base_env: Mapping[str, str] | None = None,
    timeout: float = 30.0,
) -> CleanMachineE2EReport:
    """Start bundled Python with external CWD, closed dependencies and state."""
    root = _canonical(root)
    cwd = _canonical(cwd)
    if not cwd.is_dir():
        raise CleanMachineE2EError(f"Clean-machine probe CWD does not exist: {cwd}")
    if root == cwd or _inside(cwd, root):
        raise CleanMachineE2EError(
            f"Clean-machine probe CWD must be outside the application root: {cwd}"
        )
    try:
        _validate_for_root(root)
    except Exception as exc:
        raise CleanMachineE2EError(
            f"Packaged runtime preflight failed: {exc}"
        ) from exc

    python = _python_path(root)
    if not python.is_file():
        raise CleanMachineE2EError(f"Portable Python is missing: {python}")
    try:
        dependency_closure.assert_artifact_owned(python, root, label="portable Python")
    except dependency_closure.DependencyClosureError as exc:
        raise CleanMachineE2EError(
            f"Portable dependency closure failed: {exc}"
        ) from exc

    requested = dict(os.environ if base_env is None else base_env)
    requested.setdefault(
        runtime_paths.STATE_ROOT_ENV,
        str(root.parent / "RoboStudio User State"),
    )
    env = _clean_environment(root, requested)
    try:
        completed = subprocess.run(
            [str(python), "-c", _PROBE],
            cwd=str(cwd),
            env=env,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CleanMachineE2EError(
            f"Portable runtime execution failed: {exc}"
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no diagnostic output"
        raise CleanMachineE2EError(
            f"Portable runtime probe failed with exit code {completed.returncode}: {detail}"
        )
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise CleanMachineE2EError(
            f"Portable runtime probe returned invalid diagnostics: {completed.stdout!r}"
        ) from exc

    observed_cwd = _canonical(result["cwd"])
    expected_python = _canonical(python)
    observed_python = _canonical(result["executable"])
    expected_payload = _canonical(root / "runtime" / "platformio")
    state_root = _canonical(result["state_root"])
    environment_verified = (
        _canonical(result["application_home"]) == root
        and result.get("runtime_mode") == "packaged"
        and result.get("dependency_mode") == "artifact-closed"
        and result.get("path_closed") is True
        and not _inside(state_root, root)
        and _inside(result["core"], state_root)
        and not _inside(result["core"], root)
        and _inside(result["cache"], state_root)
        and not _inside(result["cache"], root)
        and _canonical(result["platforms"]) == _canonical(expected_payload / "platforms")
        and _canonical(result["packages"]) == _canonical(expected_payload / "packages")
        and not result.get("host_pythonhome_present")
        and not result.get("host_pythonpath_present")
        and not result.get("host_virtualenv_present")
        and not result.get("host_nodepath_present")
        and not result.get("host_npm_prefix_present")
        and not result.get("host_piohome_present")
    )
    executable_verified = observed_python == expected_python and _inside(observed_python, root)
    if observed_cwd != cwd:
        raise CleanMachineE2EError(
            f"Portable runtime changed its working directory: expected {cwd}, got {observed_cwd}"
        )
    if observed_python != expected_python:
        raise CleanMachineE2EError(
            f"Portable runtime executable mismatch: expected {expected_python}, got {observed_python}"
        )
    if not executable_verified:
        raise CleanMachineE2EError(
            f"Portable runtime escaped application root: expected {root}, got {observed_python}"
        )
    if not environment_verified:
        raise CleanMachineE2EError(
            "Portable runtime inherited host state or violated dependency/state isolation"
        )
    return CleanMachineE2EReport(
        root,
        python,
        cwd,
        completed.returncode,
        executable_verified,
        environment_verified,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate portable RoboStudio runtime execution"
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--cwd", type=Path, required=True)
    args = parser.parse_args()
    report = execute_clean_machine_probe(args.root, cwd=args.cwd)
    print("RoboStudio clean-machine execution: PASS")
    print(f"Portable Python: {report.python}")
    print(f"External CWD: {report.cwd}")
