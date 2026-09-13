"""RSD-09 release artifact and relocation smoke tests."""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, release_package, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except release_package.ReleasePackageError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_distribution(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "RoboStudio.exe").write_bytes(b"fake-robo-studio")
    # RSD-15 makes the application version an explicit release input. Keep the
    # RSD-09 fixture aligned with the current distribution manifest contract.
    (root / "VERSION").write_text("0.1.1\n", encoding="utf-8")
    (root / "runtime" / "bin").mkdir(parents=True)
    (root / "runtime" / "bin" / "python.exe").write_bytes(b"portable-python")
    core = root / "runtime" / "platformio"
    (core / "platforms" / "espressif32").mkdir(parents=True)
    (core / "packages" / "tool-esptoolpy").mkdir(parents=True)
    (root / "runtime" / "platformio" / "deployment-runtime.json").write_text(
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
                    "python": "runtime/bin/python.exe",
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
    resources = root / "runtime" / "resources"
    profile = resources / "robot-isa" / "target_profiles.json"
    profile.parent.mkdir(parents=True)
    profile.write_text('{"targets": []}\n', encoding="utf-8")
    runtime_resources.write_resource_manifest(resources)
    (root / distribution_package.DISTRIBUTION_MANIFEST).write_text(
        json.dumps(
            {
                "schema": distribution_package.SCHEMA,
                "schema_version": distribution_package.SCHEMA_VERSION,
                "application": "RoboStudio.exe",
                "portable": True,
                "artifact_model": "legacy-runtime",
                "production_boundary": False,
                "runtime_root": "runtime",
                "files": [
                    {"path": "RoboStudio.exe", "size": 16, "sha256": ""},
                ],
            }
        ),
        encoding="utf-8",
    )
    # Generate the authoritative file list while preserving the legacy-runtime
    # fixture semantics. This keeps RSD-09 aligned with the current schema.
    manifest = json.loads((root / distribution_package.DISTRIBUTION_MANIFEST).read_text(encoding="utf-8"))
    manifest["files"] = distribution_package._file_entries(root)
    (root / distribution_package.DISTRIBUTION_MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return root


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        distribution = make_distribution(base / "distribution")
        artifact = base / "release" / "RoboStudio-Windows.zip"

        result = release_package.build_release(distribution, artifact)
        check("release artifact is created", result.artifact.is_file())
        check("release manifest is created", result.manifest.is_file())
        check("release artifact has expected payload", result.file_count >= 5)
        manifest = release_package.validate_release_artifact(artifact, result.manifest)
        check("release artifact validates", manifest["portable"] is True)
        check("release manifest records artifact checksum", len(manifest["artifact_sha256"]) == 64)

        with zipfile.ZipFile(artifact) as archive:
            names = archive.namelist()
            check("release paths are relative", all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in names))
            check("host-specific penv is absent", not any(part.lower() == "penv" for n in names for part in Path(n).parts))
            check("distribution manifest is shipped", distribution_package.DISTRIBUTION_MANIFEST in names)
            check("portable Python is shipped", "runtime/bin/python.exe" in names)
            check("PlatformIO runtime is shipped", "runtime/platformio/deployment-runtime.json" in names)
            check("runtime resource is shipped", "runtime/resources/robot-isa/target_profiles.json" in names)

        extracted = base / "clean-machine" / "RoboStudio"
        extracted.mkdir(parents=True)
        with zipfile.ZipFile(artifact) as archive:
            archive.extractall(extracted)
        check("artifact can be relocated outside source tree", (extracted / "RoboStudio.exe").is_file())
        check("relocated runtime keeps portable Python", (extracted / "runtime" / "bin" / "python.exe").is_file())
        check("relocated runtime keeps PlatformIO", (extracted / "runtime" / "platformio").is_dir())

        tampered = base / "tampered.zip"
        tampered.write_bytes(artifact.read_bytes() + b"tamper")
        expect_error("artifact checksum drift is rejected", lambda: release_package.validate_release_artifact(tampered, result.manifest), "checksum mismatch")

        bad = base / "bad-distribution"
        make_distribution(bad)
        (bad / "runtime" / "platformio" / "penv").mkdir()
        expect_error("host-specific distribution is rejected", lambda: release_package.build_release(bad, base / "bad.zip"), "penv")

    print("RSD-09 release artifact checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
