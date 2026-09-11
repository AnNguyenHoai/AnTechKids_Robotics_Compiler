"""RSD-08 regression tests for clean-machine packaged launch."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_launch, runtime_preflight, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def make_distribution(root: Path) -> None:
    (root / "runtime" / "bin").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "platformio" / "platforms").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "platformio" / "packages").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "resources" / "robot-isa").mkdir(parents=True, exist_ok=True)
    (root / "RoboStudio.exe").write_bytes(b"fake-robo-studio")
    (root / "runtime" / "bin" / "python.exe").write_bytes(b"fake-python")
    (root / "runtime" / "platformio" / "deployment-runtime.json").write_text(
        json.dumps(
            {
                "schema": "antechkids.robostudio.deployment-runtime",
                "schema_version": 1,
                "portable_python_required": True,
                "host_virtualenv_included": False,
                "runtime_layout": {
                    "core_dir": "runtime/platformio",
                    "python": "runtime/bin/python.exe",
                },
                "platformio_core": {"required_directories": ["platforms", "packages"]},
            }
        ),
        encoding="utf-8",
    )
    (root / "runtime" / "resources" / "robot-isa" / "target_profiles.json").write_text(
        "{}\n", encoding="utf-8"
    )
    runtime_resources.write_resource_manifest(root / "runtime" / "resources")
    (root / "distribution-manifest.json").write_text(
        json.dumps(
            {
                "schema": "antechkids.robostudio.distribution",
                "schema_version": 1,
                "application": "RoboStudio.exe",
            }
        ),
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "RoboStudio"
        root.mkdir()
        make_distribution(root)

        old_home = os.environ.get("ROBOSTUDIO_HOME")
        try:
            os.environ["ROBOSTUDIO_HOME"] = str(root)
            report = runtime_preflight.validate_distribution(root)
            check("clean-machine fixture passes runtime preflight", report.application_root == root)

            hostile = {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONHOME": "C:\\HostPython",
                "PYTHONPATH": "C:\\HostProject",
                "VIRTUAL_ENV": "C:\\HostVenv",
                "CONDA_PREFIX": "C:\\HostConda",
                "PIOHOME_DIR": "C:\\HostPlatformIO",
                "PLATFORMIO_CORE_DIR": "C:\\HostPlatformIO",
                "PLATFORMIO_PACKAGES_DIR": "C:\\HostPackages",
            }
            env = distribution_launch.clean_machine_environment(root, hostile)
            host_only = {"PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX", "PIOHOME_DIR"}
            check("host-only runtime variables are removed", all(name not in env for name in host_only))
            check("application home is explicit", env["ROBOSTUDIO_HOME"] == str(root))
            check("PlatformIO core is application-owned", env["PLATFORMIO_CORE_DIR"] == str(root / "runtime" / "platformio"))
            check("PlatformIO packages are application-owned", env["PLATFORMIO_PACKAGES_DIR"] == str(root / "runtime" / "platformio" / "packages"))
            check("host PATH is preserved", env["PATH"] == hostile["PATH"])

            external_cwd = Path(temp) / "outside"
            external_cwd.mkdir()
            spec = distribution_launch.build_launch_spec(root, cwd=external_cwd, base_env=hostile)
            check("launch command uses absolute application executable", spec.command[0] == str(root / "RoboStudio.exe"))
            check("launch cwd is external to application", spec.cwd == external_cwd and not spec.cwd.is_relative_to(root))
            check("launch manifest is generated", distribution_launch.write_launch_manifest(root).is_file())

            manifest = json.loads((root / distribution_launch.LAUNCH_MANIFEST).read_text(encoding="utf-8"))
            check("launch manifest records PATH independence", manifest["path_lookup_required"] is False)
            check("launch manifest records external cwd", manifest["cwd_must_be_external"] is True)
        finally:
            if old_home is None:
                os.environ.pop("ROBOSTUDIO_HOME", None)
            else:
                os.environ["ROBOSTUDIO_HOME"] = old_home

    print("RSD-08 clean-machine launch checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
