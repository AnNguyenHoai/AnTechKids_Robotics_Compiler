"""RSD-12 end-to-end portable release acceptance tests."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, portable_release_gate, release_package, runtime_paths


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except portable_release_gate.PortableReleaseGateError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def make_inputs(root: Path) -> distribution_package.DistributionInputs:
    root.mkdir(parents=True, exist_ok=True)
    executable = root / "RoboStudio.exe"
    executable.write_bytes(b"fake-robo-studio")
    (root / "VERSION").write_text("0.1.1\n", encoding="utf-8")

    runtime_bin = root / "runtime-bin"
    runtime_bin.mkdir()
    (runtime_bin / "python.exe").write_bytes(b"fake-python")

    runtime_platformio = root / "runtime-platformio"
    (runtime_platformio / "platforms").mkdir(parents=True)
    (runtime_platformio / "packages").mkdir(parents=True)
    (runtime_platformio / "deployment-runtime.json").write_text(
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
                "platformio_core": {
                    "required_directories": ["platforms", "packages"]
                },
            }
        ),
        encoding="utf-8",
    )

    runtime_resources = root / "runtime-resources"
    target = runtime_resources / "robot-isa"
    target.mkdir(parents=True)
    (target / "target_profiles.json").write_text("{}\n", encoding="utf-8")

    return distribution_package.DistributionInputs(
        executable=executable,
        runtime_bin=runtime_bin,
        runtime_platformio=runtime_platformio,
        runtime_resources=runtime_resources,
    )


def main() -> int:
    original_env = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = make_inputs(root / "inputs")
            distribution = root / "distribution"
            distribution_package.assemble_distribution(inputs, distribution)
            artifact = root / "RoboStudio-portable.zip"
            result = release_package.build_release(distribution, artifact)

            hostile = dict(original_env)
            hostile.update(
                {
                    "PATH": "C:\\HostOnly\\bin",
                    "PYTHONHOME": "C:\\HostPython",
                    "PYTHONPATH": "C:\\HostProject",
                    "VIRTUAL_ENV": "C:\\HostVenv",
                    "PIOHOME_DIR": "C:\\HostPlatformIO",
                    "PLATFORMIO_CORE_DIR": "C:\\HostPlatformIO",
                    "PLATFORMIO_PLATFORMS_DIR": "C:\\HostPlatforms",
                    "PLATFORMIO_PACKAGES_DIR": "C:\\HostPackages",
                    "PLATFORMIO_WORKSPACE_DIR": "C:\\HostWorkspace",
                }
            )

            report = portable_release_gate.validate_release_artifact(
                result.artifact,
                result.manifest,
                base_env=hostile,
            )
            check("release artifact passes end-to-end acceptance", report.relocation_verified)
            check("release application is recorded", report.application == "RoboStudio.exe")
            check("release payload is non-empty", report.file_count > 0)
            check("build workspace is outside relocated application", report.build_workspace not in report.relocated_root.parents)
            check("build workspace is under user-owned data", report.build_workspace.name == "platformio")

            expect_error(
                "missing release artifact is rejected",
                lambda: portable_release_gate.validate_release_artifact(root / "missing.zip"),
                "artifact not found",
            )

            tampered = root / "tampered.zip"
            tampered.write_bytes(result.artifact.read_bytes() + b"drift")
            expect_error(
                "release checksum drift is rejected by acceptance gate",
                lambda: portable_release_gate.validate_release_artifact(tampered, result.manifest),
                "checksum",
            )

            before = result.artifact.read_bytes()
            portable_release_gate.validate_release_artifact(result.artifact, result.manifest)
            check("acceptance gate does not mutate release artifact", result.artifact.read_bytes() == before)
            check(
                "application identity is restored after gate",
                os.environ.get(runtime_paths.APPLICATION_HOME_ENV) == original_env.get(runtime_paths.APPLICATION_HOME_ENV),
            )

        print("RSD-12 portable release acceptance checks: PASS")
        return 0
    finally:
        os.environ.clear()
        os.environ.update(original_env)


if __name__ == "__main__":
    raise SystemExit(main())
