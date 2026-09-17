"""RSD-21.3 production artifact boundary regression suite."""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, production_artifact_boundary, production_distribution, release_package


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _minimal_pe() -> bytes:
    data = bytearray(0x600)
    data[0:2] = b"MZ"
    data[0x3C:0x40] = (0x80).to_bytes(4, "little")
    data[0x80:0x84] = b"PE\0\0"
    data[0x84:0x86] = (0x8664).to_bytes(2, "little")
    data[0x86:0x88] = (1).to_bytes(2, "little")
    data[0x94:0x96] = (0xF0).to_bytes(2, "little")
    section = 0x80 + 24 + 0xF0
    data[section:section + 8] = b".text\0\0\0"
    data[section + 8:section + 12] = (0x200).to_bytes(4, "little")
    data[section + 12:section + 16] = (0x1000).to_bytes(4, "little")
    data[section + 16:section + 20] = (0x200).to_bytes(4, "little")
    data[section + 20:section + 24] = (0x400).to_bytes(4, "little")
    return bytes(data)


def _resources(root: Path) -> Path:
    resources = root / "resources"
    (resources / "robot-isa").mkdir(parents=True)
    (resources / "robot-isa" / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")
    return resources


def _runtime_fixture(root: Path) -> tuple[Path, Path]:
    """Create the smallest valid application-owned Python + PlatformIO runtime."""
    runtime_bin = root / "runtime-bin"
    (runtime_bin / "Lib" / "site-packages" / "platformio").mkdir(parents=True)
    (runtime_bin / "python.exe").write_bytes(b"application-owned python runtime")
    (runtime_bin / "Lib" / "site-packages" / "platformio" / "__init__.py").write_text(
        "__version__ = 'fixture'\n", encoding="utf-8"
    )

    runtime_platformio = root / "runtime-platformio"
    (runtime_platformio / "platforms" / "espressif32").mkdir(parents=True)
    (runtime_platformio / "packages" / "tool-esptoolpy").mkdir(parents=True)
    return runtime_bin, runtime_platformio


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd21-3-") as temp:
        base = Path(temp)
        source = base / "source"
        source.mkdir()
        executable = source / "RoboStudio.exe"
        executable.write_bytes(_minimal_pe())
        (source / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        resources = _resources(source)
        runtime_bin, runtime_platformio = _runtime_fixture(source)
        output = base / "distribution"

        default_inputs = production_distribution.ProductionDistributionInputs(
            executable=executable,
            runtime_resources=resources,
            version_file=source / "VERSION",
            runtime_bin=runtime_bin,
            runtime_platformio=runtime_platformio,
        )
        result = production_distribution.build_production_distribution(default_inputs, output)
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
        check("bundled PlatformIO platforms are packaged", (output / "runtime" / "platformio" / "platforms").is_dir())
        check("bundled PlatformIO packages are packaged", (output / "runtime" / "platformio" / "packages").is_dir())
        check(
            "bundled PlatformIO deployment manifest is packaged",
            (output / "runtime" / "platformio" / "deployment-runtime.json").is_file(),
        )
        boundary = json.loads((output / production_artifact_boundary.BOUNDARY_MANIFEST).read_text(encoding="utf-8"))
        check("boundary evidence is PASS", boundary["status"] == "PASS")
        check(
            "boundary artifact model is application-owned runtime",
            boundary["artifact_model"] == "RoboStudio + Compiler + Application-Owned Runtime",
        )

        explicit = production_distribution.ProductionDistributionInputs(
            executable=executable,
            runtime_resources=resources,
            version_file=source / "VERSION",
            runtime_bin=runtime_bin,
            runtime_platformio=runtime_platformio,
            compiler_root=ROOT / "robot-compiler",
            frontend_root=ROOT / "robot-frontend-robosim" / "frontend",
        )
        check(
            "explicit application roots remain valid",
            production_distribution.validate_inputs(explicit, base / "explicit-validation") == "1.2.3",
        )

        artifact = base / "RoboStudio-1.2.3-Windows.zip"
        release = release_package.build_release(output, artifact)
        check("production ZIP is created", artifact.is_file())
        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
        check("ZIP contains RoboStudio", "RoboStudio.exe" in names)
        check("ZIP contains application resources", "runtime/resources/robot-isa/target_profiles.json" in names)
        check("ZIP contains boundary evidence", production_artifact_boundary.BOUNDARY_MANIFEST in names)
        check("ZIP contains bundled Python", "runtime/bin/python.exe" in names)
        check(
            "ZIP contains bundled PlatformIO",
            "runtime/platformio/deployment-runtime.json" in names
            and "runtime/bin/Lib/site-packages/platformio/__init__.py" in names,
        )

        manifest = json.loads(release.manifest.read_text(encoding="utf-8"))
        compatibility = manifest["compatibility"]
        check("release does not require host Python", compatibility["portable_python_required"] is False)
        check("release does not require host PlatformIO", compatibility["bundled_platformio_required"] is False)

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
