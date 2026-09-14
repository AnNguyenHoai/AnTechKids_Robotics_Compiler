"""RSD-15 release compatibility contract tests."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, release_compatibility, release_package, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except release_compatibility.ReleaseCompatibilityError as exc:
        check(name, expected in str(exc))
    except release_package.ReleasePackageError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_distribution(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "RoboStudio.exe").write_bytes(b"fake-robo-studio")
    (root / "VERSION").write_text("0.1.1\n", encoding="utf-8")

    runtime_bin = root / "runtime" / "bin"
    runtime_bin.mkdir(parents=True)
    (runtime_bin / "python.exe").write_bytes(b"portable-python")

    core = root / "runtime" / "platformio"
    (core / "platforms" / "espressif32").mkdir(parents=True)
    (core / "packages" / "tool-esptoolpy").mkdir(parents=True)
    (core / "deployment-runtime.json").write_text(
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

    files = distribution_package._file_entries(root)
    manifest = {
        "schema": distribution_package.SCHEMA,
        "schema_version": distribution_package.SCHEMA_VERSION,
        "application": "RoboStudio.exe",
        "portable": True,
        "runtime_root": "runtime",
        "files": files,
    }
    (root / distribution_package.DISTRIBUTION_MANIFEST).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return root


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd15-") as temp:
        base = Path(temp)
        distribution = make_distribution(base / "distribution")
        artifact = base / "release" / "RoboStudio-Windows.zip"
        result = release_package.build_release(distribution, artifact)

        manifest = release_package.validate_release_artifact(artifact, result.manifest)
        compatibility = manifest["compatibility"]
        check("compatibility contract is shipped", isinstance(compatibility, dict))
        check("compatibility schema is declared", compatibility["schema"] == release_compatibility.SCHEMA)
        check("compatibility schema version is declared", compatibility["schema_version"] == 1)
        check("application version is locked", compatibility["application_version"] == "0.1.1")
        check("runtime schema is locked", compatibility["runtime_integrity_schema_version"] == 1)
        check("distribution schema is locked", compatibility["distribution_schema_version"] == distribution_package.SCHEMA_VERSION == 2)
        check("release schema is locked", compatibility["release_schema_version"] == 1)
        check("portable Python is mandatory", compatibility["portable_python_required"] is True)
        check("bundled PlatformIO is mandatory", compatibility["bundled_platformio_required"] is True)

        checked = release_package.validate_release_compatibility(
            manifest,
            application_version="0.1.1",
            runtime_integrity_schema_version=1,
            distribution_schema_version=2,
            release_schema_version=1,
        )
        check("matching runtime compatibility is accepted", checked.application_version == "0.1.1")

        expect_error(
            "major application drift is rejected",
            lambda: release_compatibility.validate_compatibility(manifest, application_version="1.0.0"),
            "Incompatible application major version",
        )
        expect_error(
            "newer release is rejected",
            lambda: release_compatibility.validate_compatibility(manifest, application_version="0.1.0"),
            "newer than runtime",
        )
        expect_error(
            "runtime schema drift is rejected",
            lambda: release_compatibility.validate_compatibility(manifest, runtime_integrity_schema_version=2),
            "runtime_integrity_schema_version",
        )
        expect_error(
            "distribution schema drift is rejected",
            lambda: release_compatibility.validate_compatibility(manifest, distribution_schema_version=3),
            "distribution_schema_version",
        )
        expect_error(
            "release schema drift is rejected",
            lambda: release_compatibility.validate_compatibility(manifest, release_schema_version=2),
            "release_schema_version",
        )

        malformed = dict(manifest)
        malformed["compatibility"] = dict(compatibility)
        malformed["compatibility"]["application_version"] = "development"
        expect_error(
            "malformed application version is rejected",
            lambda: release_compatibility.read_compatibility(malformed),
            "Invalid release application version",
        )

        missing = dict(manifest)
        missing.pop("compatibility")
        expect_error(
            "missing compatibility contract is rejected",
            lambda: release_compatibility.read_compatibility(missing),
            "no compatibility contract",
        )

        disabled = dict(manifest)
        disabled["compatibility"] = dict(compatibility)
        disabled["compatibility"]["portable_python_required"] = False
        expect_error(
            "non-portable Python requirement is rejected",
            lambda: release_compatibility.read_compatibility(disabled),
            "portable Python",
        )

    print("RSD-15 release compatibility checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
