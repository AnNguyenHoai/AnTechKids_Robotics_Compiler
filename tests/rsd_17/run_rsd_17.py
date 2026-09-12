"""RSD-17 production distribution builder tests."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_distribution, runtime_preflight


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except production_distribution.ProductionDistributionError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_inputs(root: Path) -> production_distribution.ProductionDistributionInputs:
    executable = root / "app-build" / "RoboStudio.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"production-executable")
    (executable.parent / "Qt6Core.dll").write_bytes(b"application-local-dll")

    version = root / "VERSION"
    version.write_text("7.2.0\n", encoding="utf-8")

    runtime_bin = root / "portable-python"
    runtime_bin.mkdir()
    (runtime_bin / "python.exe").write_bytes(b"portable-python")

    platformio = root / "platformio-runtime"
    (platformio / "platforms" / "espressif32").mkdir(parents=True)
    (platformio / "packages" / "tool-esptoolpy").mkdir(parents=True)
    (platformio / "deployment-runtime.json").write_text(
        json.dumps(
            {
                "schema": "antechkids.robostudio.deployment-runtime",
                "schema_version": 1,
                "platformio_core": {
                    "source_not_embedded": True,
                    "required_directories": ["platforms", "packages"],
                    "file_count": 0,
                },
                "runtime_layout": {
                    "core_dir": "runtime/platformio",
                    "python": "runtime/bin/python.exe" if sys.platform == "win32" else "runtime/bin/python",
                    "platformio_module": "platformio",
                },
                "portable_python_required": True,
                "host_virtualenv_included": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    resources = root / "resources"
    profile = resources / "robot-isa" / "target_profiles.json"
    profile.parent.mkdir(parents=True)
    profile.write_text('{"targets": []}\n', encoding="utf-8")

    from tools import runtime_resources
    runtime_resources.write_resource_manifest(resources)

    return production_distribution.ProductionDistributionInputs(
        executable=executable,
        runtime_bin=runtime_bin,
        runtime_platformio=platformio,
        runtime_resources=resources,
        version_file=version,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd17-") as temp:
        root = Path(temp)
        inputs = make_inputs(root)
        output = root / "distribution"

        old_cwd = Path.cwd()
        os.chdir(root / "app-build")
        try:
            result = production_distribution.build_production_distribution(inputs, output)
        finally:
            os.chdir(old_cwd)

        check("production distribution is created", result.distribution_root.is_dir())
        check("application is copied", (output / "RoboStudio.exe").is_file())
        check("application-local DLL is copied", (output / "Qt6Core.dll").is_file())
        check("repository VERSION is integrated", (output / "VERSION").read_text(encoding="utf-8").strip() == "7.2.0")
        check("portable Python is included", (output / "runtime" / "bin" / "python.exe").is_file())
        check("PlatformIO runtime is included", (output / "runtime" / "platformio" / "deployment-runtime.json").is_file())
        check("runtime resources are included", (output / "runtime" / "resources" / "robot-isa" / "target_profiles.json").is_file())
        check("distribution passes runtime preflight", runtime_preflight.validate_distribution(output).application_root == output)

        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
        check("distribution manifest records application", manifest["application"] == "RoboStudio.exe")
        check("distribution manifest records portability", manifest["portable"] is True)
        check("distribution manifest records application-local DLL", any(item["path"] == "Qt6Core.dll" for item in manifest["files"]))
        check("distribution VERSION is not source-relative", Path(manifest["files"][0]["path"]).is_absolute() is False)

        missing_version = production_distribution.ProductionDistributionInputs(
            executable=inputs.executable,
            runtime_bin=inputs.runtime_bin,
            runtime_platformio=inputs.runtime_platformio,
            runtime_resources=inputs.runtime_resources,
            version_file=root / "missing-VERSION",
        )
        expect_error(
            "missing production VERSION is rejected",
            lambda: production_distribution.build_production_distribution(missing_version, root / "bad-version"),
            "VERSION",
        )

        bad_platformio = root / "bad-platformio"
        (bad_platformio / "platforms").mkdir(parents=True)
        (bad_platformio / "packages").mkdir(parents=True)
        (bad_platformio / "penv").mkdir()
        bad_inputs = production_distribution.ProductionDistributionInputs(
            executable=inputs.executable,
            runtime_bin=inputs.runtime_bin,
            runtime_platformio=bad_platformio,
            runtime_resources=inputs.runtime_resources,
            version_file=inputs.version_file,
        )
        expect_error(
            "host-specific PlatformIO penv is rejected",
            lambda: production_distribution.build_production_distribution(bad_inputs, root / "bad-penv"),
            "penv",
        )

    print("RSD-17 production distribution checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
