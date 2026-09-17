"""RSD-21.3 production artifact boundary regression suite."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.rsd_17.run_rsd_17 import make_inputs
from tools import production_artifact_boundary, production_distribution, release_package


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd21-3-") as temp:
        base = Path(temp)
        inputs = make_inputs(base)
        output = base / "distribution"

        old_cwd = Path.cwd()
        os.chdir(base / "app-build")
        try:
            result = production_distribution.build_production_distribution(inputs, output)
        finally:
            os.chdir(old_cwd)

        check("production distribution is created", result.distribution_root.is_dir())
        check("RoboStudio is packaged", (output / "RoboStudio.exe").is_file())
        check(
            "application resources are packaged",
            (output / "runtime" / "resources" / "robot-isa" / "target_profiles.json").is_file(),
        )
        check("bundled Python runtime is packaged", (output / "runtime" / "bin" / "python.exe").is_file())
        check(
            "bundled PlatformIO Python package is packaged",
            (output / "runtime" / "bin" / "Lib" / "site-packages" / "platformio" / "__init__.py").is_file(),
        )
        check(
            "bundled PlatformIO platforms are packaged",
            (output / "runtime" / "platformio" / "platforms").is_dir(),
        )
        check(
            "bundled PlatformIO packages are packaged",
            (output / "runtime" / "platformio" / "packages").is_dir(),
        )
        check(
            "bundled PlatformIO deployment manifest is packaged",
            (output / "runtime" / "platformio" / "deployment-runtime.json").is_file(),
        )
        check(
            "production firmware is packaged",
            (output / "firmware" / "robot-platform" / "platformio.ini").is_file(),
        )

        boundary = json.loads(
            (output / production_artifact_boundary.BOUNDARY_MANIFEST).read_text(encoding="utf-8")
        )
        check("boundary evidence is PASS", boundary["status"] == "PASS")
        check(
            "boundary artifact model is application-owned runtime",
            boundary["artifact_model"] == "RoboStudio + Compiler + Application-Owned Runtime",
        )

        explicit = production_distribution.ProductionDistributionInputs(
            executable=inputs.executable,
            runtime_resources=inputs.runtime_resources,
            version_file=inputs.version_file,
            runtime_bin=inputs.runtime_bin,
            runtime_platformio=inputs.runtime_platformio,
            compiler_root=inputs.compiler_root,
            frontend_root=inputs.frontend_root,
            firmware_root=inputs.firmware_root,
        )
        check(
            "explicit application roots remain valid",
            production_distribution.validate_inputs(explicit, base / "explicit-validation") == "7.2.0",
        )

        artifact = base / "RoboStudio-7.2.0-Windows.zip"
        release = release_package.build_release(output, artifact)
        check("production ZIP is created", artifact.is_file())
        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
        check("ZIP contains RoboStudio", "RoboStudio.exe" in names)
        check(
            "ZIP contains application resources",
            "runtime/resources/robot-isa/target_profiles.json" in names,
        )
        check(
            "ZIP contains boundary evidence",
            production_artifact_boundary.BOUNDARY_MANIFEST in names,
        )
        check("ZIP contains bundled Python", "runtime/bin/python.exe" in names)
        check(
            "ZIP contains bundled PlatformIO",
            "runtime/platformio/deployment-runtime.json" in names
            and "runtime/bin/Lib/site-packages/platformio/__init__.py" in names,
        )
        check(
            "ZIP contains production firmware",
            "firmware/robot-platform/platformio.ini" in names,
        )

        manifest = json.loads(release.manifest.read_text(encoding="utf-8"))
        compatibility = manifest["compatibility"]
        check(
            "release does not require host Python",
            compatibility["portable_python_required"] is False,
        )
        check(
            "release does not require host PlatformIO",
            compatibility["bundled_platformio_required"] is False,
        )

        forbidden = output / ".pio" / "unexpected-build-state"
        forbidden.mkdir(parents=True)
        try:
            production_artifact_boundary.validate_distribution_root(output)
        except production_artifact_boundary.ProductionArtifactBoundaryError as exc:
            check("developer-only payload is rejected", ".pio" in str(exc))
        else:
            raise AssertionError("developer-only payload unexpectedly accepted")

    print("RSD-21.3 production artifact boundary checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
