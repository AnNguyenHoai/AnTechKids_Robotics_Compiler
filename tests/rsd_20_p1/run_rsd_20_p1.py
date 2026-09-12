"""RSD-20-P.1 production release artifact assembly tests."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_release_assembly


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except production_release_assembly.ProductionReleaseAssemblyError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_inputs(root: Path) -> production_release_assembly.ProductionReleaseInputs:
    executable = root / "upstream-build" / "RoboStudio.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"production-executable")

    version = root / "VERSION"
    version.write_text("7.2.0\n", encoding="utf-8")

    runtime_bin = root / "portable-python"
    runtime_bin.mkdir()
    python_name = "python.exe" if sys.platform == "win32" else "python"
    (runtime_bin / python_name).write_bytes(b"portable-python")

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
                    "python": f"runtime/bin/{python_name}",
                    "platformio_module": "platformio",
                },
                "portable_python_required": True,
                "host_virtualenv_included": False,
            }
        ) + "\n",
        encoding="utf-8",
    )

    resources = root / "resources"
    profile = resources / "robot-isa" / "target_profiles.json"
    profile.parent.mkdir(parents=True)
    profile.write_text('{"targets": []}\n', encoding="utf-8")
    from tools import runtime_resources
    runtime_resources.write_resource_manifest(resources)

    return production_release_assembly.ProductionReleaseInputs(
        executable=executable,
        runtime_bin=runtime_bin,
        runtime_platformio=platformio,
        runtime_resources=resources,
        version_file=version,
        source_revision="test-revision",
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd20p1-") as temp:
        root = Path(temp)
        inputs = make_inputs(root)
        output = root / "release-output"

        old_cwd = Path.cwd()
        os.chdir(root)
        try:
            report = production_release_assembly.assemble_release(inputs, output)
        finally:
            os.chdir(old_cwd)

        artifact = output / "RoboStudio-7.2.0-Windows.zip"
        check("production release artifact is created", artifact.is_file())
        check("release artifact has non-zero size", artifact.stat().st_size > 0)
        check("release manifest is created", (output / "release-manifest.json").is_file())
        check("provenance sidecar is created", (output / "release-provenance.json").is_file())
        check("portable proof report is created", (output / "portable-release-proof.json").is_file())
        check("assembly report is created", (output / "release-assembly-report.json").is_file())
        check("assembly report is PASS", report["status"] == "PASS")
        check("assembly report records source revision", report["source_revision"] == "test-revision")
        check("assembly report records artifact SHA-256", len(report["artifact_sha256"]) == 64)

        manifest = json.loads((output / "release-manifest.json").read_text(encoding="utf-8"))
        check("release is declared portable", manifest["portable"] is True)
        check("release version is deterministic", manifest["application_version"] == "7.2.0")

        missing = production_release_assembly.ProductionReleaseInputs(
            executable=root / "missing.exe",
            runtime_bin=inputs.runtime_bin,
            runtime_platformio=inputs.runtime_platformio,
            runtime_resources=inputs.runtime_resources,
            version_file=inputs.version_file,
            source_revision=inputs.source_revision,
        )
        expect_error(
            "missing executable is rejected before assembly",
            lambda: production_release_assembly.assemble_release(missing, root / "bad-output"),
            "RoboStudio executable",
        )

        invalid_version = root / "bad-version"
        invalid_version.write_text("7.2.0/evil\n", encoding="utf-8")
        bad_version_inputs = production_release_assembly.ProductionReleaseInputs(
            executable=inputs.executable,
            runtime_bin=inputs.runtime_bin,
            runtime_platformio=inputs.runtime_platformio,
            runtime_resources=inputs.runtime_resources,
            version_file=invalid_version,
            source_revision=inputs.source_revision,
        )
        expect_error(
            "unsafe version is rejected",
            lambda: production_release_assembly.assemble_release(bad_version_inputs, root / "bad-version-output"),
            "Invalid application VERSION",
        )

    print("RSD-20-P.1 production release assembly checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
