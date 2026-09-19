"""RSD-07 portable distribution assembly tests."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, runtime_preflight, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except distribution_package.DistributionPackageError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_inputs(root: Path) -> distribution_package.DistributionInputs:
    executable = root / "RoboStudio.exe"
    executable.write_bytes(b"fake-executable")

    runtime_bin = root / "input-bin"
    runtime_bin.mkdir()
    (runtime_bin / "python.exe").write_bytes(b"portable-python")

    runtime_platformio = root / "input-platformio"
    (runtime_platformio / "platforms" / "espressif32").mkdir(parents=True)
    (runtime_platformio / "packages" / "tool-esptoolpy").mkdir(parents=True)
    deployment_manifest = {
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
    }
    (runtime_platformio / "deployment-runtime.json").write_text(
        json.dumps(deployment_manifest, indent=2) + "\n", encoding="utf-8"
    )

    runtime_resource_root = root / "input-resources"
    profile = runtime_resource_root / "robot-isa" / "target_profiles.json"
    profile.parent.mkdir(parents=True)
    profile.write_text('{"targets": []}\n', encoding="utf-8")
    runtime_resources.write_resource_manifest(runtime_resource_root)

    return distribution_package.DistributionInputs(
        executable=executable,
        runtime_bin=runtime_bin,
        runtime_platformio=runtime_platformio,
        runtime_resources=runtime_resource_root,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        inputs = make_inputs(root)
        output = root / "RoboStudio"

        manifest_path = distribution_package.assemble_distribution(inputs, output)
        check("distribution manifest is created", manifest_path.is_file())
        check("RoboStudio executable is copied", (output / "RoboStudio.exe").is_file())
        check("portable Python is copied", (output / "runtime" / "bin" / "python.exe").is_file())
        check("PlatformIO runtime is copied", (output / "runtime" / "platformio" / "platforms" / "espressif32").is_dir())
        check("resource is copied", (output / "runtime" / "resources" / "robot-isa" / "target_profiles.json").is_file())
        check("assembled output passes RSD-06 preflight", runtime_preflight.validate_distribution(output).application_root == output)
        check("distribution manifest validates", distribution_package.validate_distribution_manifest(manifest_path)["portable"] is True)

        stale = output / "stale-host-file.txt"
        stale.write_text("must disappear", encoding="utf-8")
        distribution_package.assemble_distribution(inputs, output)
        check("reassembly removes stale files", not stale.exists())

        contaminated_platformio = root / "contaminated-platformio"
        (contaminated_platformio / "platforms").mkdir(parents=True)
        (contaminated_platformio / "packages").mkdir()
        (contaminated_platformio / "penv" / "Scripts").mkdir(parents=True)
        (contaminated_platformio / "penv" / "Scripts" / "python.exe").write_bytes(b"host-venv")
        source_manifest = inputs.runtime_platformio / "deployment-runtime.json"
        (contaminated_platformio / "deployment-runtime.json").write_text(
            source_manifest.read_text(encoding="utf-8"), encoding="utf-8"
        )
        contaminated_inputs = distribution_package.DistributionInputs(
            executable=inputs.executable,
            runtime_bin=inputs.runtime_bin,
            runtime_platformio=contaminated_platformio,
            runtime_resources=inputs.runtime_resources,
        )
        filtered_output = root / "filtered-output"
        filtered_manifest = distribution_package.assemble_distribution(contaminated_inputs, filtered_output)
        check("host-specific penv is filtered at distribution boundary", not (filtered_output / "runtime" / "platformio" / "penv").exists())
        check("filtered PlatformIO runtime remains valid", runtime_preflight.validate_distribution(filtered_output).application_root == filtered_output)
        check("filtered distribution manifest validates", distribution_package.validate_distribution_manifest(filtered_manifest)["portable"] is True)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        target_entry = next(item for item in manifest["files"] if item["path"].endswith("target_profiles.json"))
        target = output / target_entry["path"]
        target.write_text("tampered\n", encoding="utf-8")
        expect_error(
            "distribution checksum drift is rejected",
            lambda: distribution_package.validate_distribution_manifest(manifest_path),
            "checksum mismatch",
        )

    print("RSD-07 portable distribution assembly checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
