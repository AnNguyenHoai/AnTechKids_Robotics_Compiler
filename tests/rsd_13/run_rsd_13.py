"""RSD-13 clean-machine end-to-end execution regression suite."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import clean_machine_e2e, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except clean_machine_e2e.CleanMachineE2EError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def make_distribution(root: Path) -> None:
    (root / "runtime" / "bin").mkdir(parents=True)
    (root / "runtime" / "platformio" / "platforms").mkdir(parents=True)
    (root / "runtime" / "platformio" / "packages").mkdir(parents=True)
    resources = root / "runtime" / "resources" / "robot-isa"
    resources.mkdir(parents=True)
    (resources / "target_profiles.json").write_text("{}\n", encoding="utf-8")
    runtime_resources.write_resource_manifest(root / "runtime" / "resources")

    python_name = "python.exe" if os.name == "nt" else "python"
    (root / "runtime" / "platformio" / "deployment-runtime.json").write_text(
        json.dumps(
            {
                "schema": "antechkids.robostudio.deployment-runtime",
                "schema_version": 1,
                "portable_python_required": True,
                "host_virtualenv_included": False,
                "runtime_layout": {
                    "core_dir": "runtime/platformio",
                    "python": f"runtime/bin/{python_name}",
                },
                "platformio_core": {"required_directories": ["platforms", "packages"]},
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    # Use the real interpreter as the portable runtime so this suite executes
    # an actual child process while remaining independent of PySide6/display.
    shutil.copy2(sys.executable, root / "runtime" / "bin" / python_name)


def main() -> int:
    original = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory(prefix="robostudio-rsd13-") as temp:
            base = Path(temp)
            distribution = base / "RoboStudio"
            external = base / "ExternalWorkspace"
            external.mkdir()
            make_distribution(distribution)

            hostile = dict(original)
            hostile.update(
                {
                    "PATH": r"C:\HostOnly\bin",
                    "PYTHONHOME": r"C:\HostPython",
                    "PYTHONPATH": r"C:\HostProject",
                    "VIRTUAL_ENV": r"C:\HostVenv",
                    "PIOHOME_DIR": r"C:\HostPlatformIO",
                    "PLATFORMIO_CORE_DIR": r"C:\HostPlatformIO",
                    "PLATFORMIO_PLATFORMS_DIR": r"C:\HostPlatforms",
                    "PLATFORMIO_PACKAGES_DIR": r"C:\HostPackages",
                    "PLATFORMIO_WORKSPACE_DIR": r"C:\HostWorkspace",
                }
            )

            report = clean_machine_e2e.execute_clean_machine_probe(
                distribution, cwd=external, base_env=hostile
            )
            check("portable Python actually executes", report.returncode == 0)
            check("child executable is application-owned", report.executable_verified)
            check("child environment is application-owned", report.environment_verified)
            check("external CWD is preserved", report.cwd == external.resolve())

            python = distribution / "runtime" / "bin" / ("python.exe" if os.name == "nt" else "python")
            python.unlink()
            expect_error(
                "missing portable interpreter is rejected before execution",
                lambda: clean_machine_e2e.execute_clean_machine_probe(distribution, cwd=external),
                "portable Python",
            )
            shutil.copy2(sys.executable, python)
            expect_error(
                "application-root CWD is rejected",
                lambda: clean_machine_e2e.execute_clean_machine_probe(distribution, cwd=distribution),
                "outside the application root",
            )

        check("clean-machine gate restores caller environment", os.environ == original)
        print("RSD-13 clean-machine execution checks: PASS")
        return 0
    finally:
        os.environ.clear()
        os.environ.update(original)


if __name__ == "__main__":
    raise SystemExit(main())
