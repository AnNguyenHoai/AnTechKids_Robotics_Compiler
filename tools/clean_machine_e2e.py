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

from tools import runtime_paths, runtime_preflight

HOST_RUNTIME_VARS = (
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


class CleanMachineE2EError(RuntimeError):
    """Raised when the portable runtime cannot execute cleanly."""


@dataclass(frozen=True)
class CleanMachineE2EReport:
    """Machine-readable result of a clean-machine runtime execution."""

    application_root: Path
    python: Path
    cwd: Path
    returncode: int
    executable_verified: bool
    environment_verified: bool


def _python_path(root: Path) -> Path:
    relative = Path("runtime") / "bin" / ("python.exe" if os.name == "nt" else "python")
    return root / relative


def _clean_environment(root: Path, base_env: Mapping[str, str] | None) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    for name in HOST_RUNTIME_VARS:
        env.pop(name, None)
    core = root / "runtime" / "platformio"
    env[runtime_paths.APPLICATION_HOME_ENV] = str(root)
    env["ROBOSTUDIO_RUNTIME_MODE"] = "packaged"
    env["PLATFORMIO_CORE_DIR"] = str(core)
    env["PLATFORMIO_PLATFORMS_DIR"] = str(core / "platforms")
    env["PLATFORMIO_PACKAGES_DIR"] = str(core / "packages")
    env["PLATFORMIO_CACHE_DIR"] = str(core / ".cache")
    env["PLATFORMIO_BUILD_CACHE_DIR"] = str(core / "build-cache")
    env["PLATFORMIO_WORKSPACE_DIR"] = str(core / "workspace")
    env["PLATFORMIO_DISABLE_UPGRADE_CHECK"] = "true"
    env["PLATFORMIO_DISABLE_PROGRESSBAR"] = "true"
    env["PLATFORMIO_NO_ANSI"] = "true"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


_PROBE = r'''
import json
import os
import sys
from pathlib import Path

root = Path(os.environ["ROBOSTUDIO_HOME"]).resolve()
expected_python = root / "runtime" / "bin" / ("python.exe" if os.name == "nt" else "python")
expected_core = root / "runtime" / "platformio"
result = {
    "executable": str(Path(sys.executable).resolve()),
    "cwd": str(Path.cwd().resolve()),
    "application_home": os.environ.get("ROBOSTUDIO_HOME"),
    "runtime_mode": os.environ.get("ROBOSTUDIO_RUNTIME_MODE"),
    "core": os.environ.get("PLATFORMIO_CORE_DIR"),
    "platforms": os.environ.get("PLATFORMIO_PLATFORMS_DIR"),
    "packages": os.environ.get("PLATFORMIO_PACKAGES_DIR"),
    "host_pythonhome_present": "PYTHONHOME" in os.environ,
    "host_pythonpath_present": "PYTHONPATH" in os.environ,
    "host_virtualenv_present": "VIRTUAL_ENV" in os.environ,
    "host_piohome_present": "PIOHOME_DIR" in os.environ,
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
    and not result["host_pythonhome_present"]
    and not result["host_pythonpath_present"]
    and not result["host_virtualenv_present"]
    and not result["host_piohome_present"]
):
    raise SystemExit(3)
'''


def _validate_for_root(root: Path) -> None:
    """Run preflight against an explicit root without depending on process env."""
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
    """Start the bundled Python process with an external CWD and clean env."""
    root = Path(root).expanduser()
    cwd = Path(cwd).expanduser()
    if not cwd.is_dir():
        raise CleanMachineE2EError(f"Clean-machine probe CWD does not exist: {cwd}")
    if root == cwd or root in cwd.parents:
        raise CleanMachineE2EError(
            f"Clean-machine probe CWD must be outside the application root: {cwd}"
        )
    try:
        _validate_for_root(root)
    except Exception as exc:
        raise CleanMachineE2EError(f"Packaged runtime preflight failed: {exc}") from exc

    python = _python_path(root)
    if not python.is_file():
        raise CleanMachineE2EError(f"Portable Python is missing: {python}")
    env = _clean_environment(root, base_env)
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
        raise CleanMachineE2EError(f"Portable runtime execution failed: {exc}") from exc

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

    observed_cwd = Path(result["cwd"]).resolve()
    expected_python = python.resolve()
    observed_python = Path(result["executable"]).resolve()
    environment_verified = (
        result.get("application_home") == str(root)
        and result.get("runtime_mode") == "packaged"
        and result.get("core") == str(root / "runtime" / "platformio")
        and result.get("platforms") == str(root / "runtime" / "platformio" / "platforms")
        and result.get("packages") == str(root / "runtime" / "platformio" / "packages")
        and not result.get("host_pythonhome_present")
        and not result.get("host_pythonpath_present")
        and not result.get("host_virtualenv_present")
        and not result.get("host_piohome_present")
    )
    executable_verified = observed_python == expected_python and expected_python.is_relative_to(root)
    if observed_cwd != cwd.resolve():
        raise CleanMachineE2EError(
            f"Portable runtime changed its working directory: expected {cwd.resolve()}, got {observed_cwd}"
        )
    if not executable_verified:
        raise CleanMachineE2EError(
            f"Portable runtime escaped application root: expected {expected_python}, got {observed_python}"
        )
    if not environment_verified:
        raise CleanMachineE2EError("Portable runtime inherited or resolved a host-owned runtime environment")

    return CleanMachineE2EReport(
        application_root=root,
        python=python,
        cwd=cwd,
        returncode=completed.returncode,
        executable_verified=executable_verified,
        environment_verified=environment_verified,
    )


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
