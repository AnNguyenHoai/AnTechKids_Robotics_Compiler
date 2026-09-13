"""RSD-21.3 production artifact boundary regression suite."""
from __future__ import annotations
import json
import sys
import tempfile
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from tools import distribution_package, production_artifact_boundary, production_distribution, release_package

def check(name: str, condition: bool) -> None:
    if not condition: raise AssertionError(name)
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

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd21-3-") as temp:
        base = Path(temp)
        source = base / "source"
        source.mkdir()
        executable = source / "RoboStudio.exe"
        executable.write_bytes(_minimal_pe())
        (source / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        resources = _resources(source)
        output = base / "distribution"
        result = production_distribution.build_production_distribution(
            production_distribution.ProductionDistributionInputs(executable, resources, source / "VERSION"), output
        )
        check("production distribution is created", result.distribution_root.is_dir())
        check("RoboStudio is packaged", (output / "RoboStudio.exe").is_file())
        check("application resources are packaged", (output / "runtime" / "resources" / "robot-isa" / "target_profiles.json").is_file())
        check("Python runtime is not packaged", not (output / "runtime" / "bin").exists())
        check("PlatformIO runtime is not packaged", not (output / "runtime" / "platformio").exists())
        boundary = json.loads((output / production_artifact_boundary.BOUNDARY_MANIFEST).read_text(encoding="utf-8"))
        check("boundary evidence is PASS", boundary["status"] == "PASS")
        check("artifact model is RoboStudio + Compiler", boundary["artifact_model"] == "RoboStudio + Compiler")

        artifact = base / "RoboStudio-1.2.3-Windows.zip"
        release = release_package.build_release(output, artifact)
        check("production ZIP is created", artifact.is_file())
        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
        check("ZIP contains RoboStudio", "RoboStudio.exe" in names)
        check("ZIP contains application resources", "runtime/resources/robot-isa/target_profiles.json" in names)
        check("ZIP contains boundary evidence", production_artifact_boundary.BOUNDARY_MANIFEST in names)
        check("ZIP excludes Python", not any(name.startswith("runtime/bin/") for name in names))
        check("ZIP excludes PlatformIO", not any(name.startswith("runtime/platformio/") for name in names))

        manifest = json.loads(release.manifest.read_text(encoding="utf-8"))
        compatibility = manifest["compatibility"]
        check("release declares host Python prerequisite", compatibility["portable_python_required"] is False)
        check("release declares host PlatformIO prerequisite", compatibility["bundled_platformio_required"] is False)

        forbidden = output / "runtime" / "platformio" / "packages"
        forbidden.mkdir(parents=True)
        try:
            production_artifact_boundary.validate_distribution_root(output)
        except production_artifact_boundary.ProductionArtifactBoundaryError as exc:
            check("bundled PlatformIO is rejected", "runtime/platformio" in str(exc))
        else:
            raise AssertionError("bundled PlatformIO unexpectedly accepted")

    print("RSD-21.3 production artifact boundary checks: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
