"""RSD-18 release provenance and reproducibility regression suite."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, release_package, release_provenance, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except ValueError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_distribution(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "RoboStudio.exe").write_bytes(b"fake-robostudio")
    (root / "VERSION").write_text("0.1.1\n", encoding="utf-8")

    runtime = root / "runtime"
    runtime_bin = runtime / "bin"
    runtime_bin.mkdir(parents=True)
    shutil.copy2(sys.executable, runtime_bin / Path(sys.executable).name)

    platformio = runtime / "platformio"
    (platformio / "platforms" / "espressif32").mkdir(parents=True)
    (platformio / "packages" / "tool-esptoolpy").mkdir(parents=True)
    (platformio / "deployment-runtime.json").write_text(
        json.dumps(
            {
                "schema": "antechkids.robostudio.deployment-runtime",
                "schema_version": 1,
                "portable_python_required": True,
                "host_virtualenv_included": False,
                "runtime_layout": {
                    "core_dir": "runtime/platformio",
                    "python": "runtime/bin/" + Path(sys.executable).name,
                },
                "platformio_core": {"required_directories": ["platforms", "packages"]},
            },
            sort_keys=True,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    resources = runtime / "resources" / "robot-isa"
    resources.mkdir(parents=True)
    (resources / "target_profiles.json").write_text("{\"targets\": []}\n", encoding="utf-8")
    runtime_resources.write_resource_manifest(runtime / "resources")

    files = distribution_package._file_entries(root)
    (root / distribution_package.DISTRIBUTION_MANIFEST).write_text(
        json.dumps(
            {
                "schema": distribution_package.SCHEMA,
                "schema_version": distribution_package.SCHEMA_VERSION,
                "application": "RoboStudio.exe",
                "portable": True,
                "runtime_root": "runtime",
                "files": files,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return root


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd18-") as temp:
        base = Path(temp)
        distribution = make_distribution(base / "distribution")
        artifact_a = base / "release-a" / "RoboStudio-Windows.zip"
        artifact_b = base / "release-b" / "RoboStudio-Windows.zip"

        first = release_package.build_release(distribution, artifact_a)
        second = release_package.build_release(distribution, artifact_b)

        check("first release artifact validates", release_package.validate_release_artifact(first.artifact) is not None)
        check("second release artifact validates", release_package.validate_release_artifact(second.artifact) is not None)
        check("repeated builds are byte-for-byte reproducible", artifact_a.read_bytes() == artifact_b.read_bytes())
        check("repeated builds have identical SHA-256", hashlib.sha256(artifact_a.read_bytes()).hexdigest() == hashlib.sha256(artifact_b.read_bytes()).hexdigest())

        provenance_a = base / "release-a" / release_provenance.PROVENANCE_MANIFEST
        provenance_b = base / "release-b" / release_provenance.PROVENANCE_MANIFEST
        release_provenance.write_provenance(
            distribution,
            first.manifest,
            first.artifact,
            provenance_a,
            source_revision="test-revision-001",
        )
        release_provenance.write_provenance(
            distribution,
            second.manifest,
            second.artifact,
            provenance_b,
            source_revision="test-revision-001",
        )
        data_a = release_provenance.validate_provenance(provenance_a, artifact_a, first.manifest)
        data_b = release_provenance.validate_provenance(provenance_b, artifact_b, second.manifest)
        check("provenance validates", data_a["source_revision"] == "test-revision-001")
        check("provenance is reproducible", provenance_a.read_bytes() == provenance_b.read_bytes())
        check("provenance records deterministic packaging", data_a["reproducibility"]["deterministic_zip"] is True)
        check("provenance records artifact checksum", data_a["artifact_sha256"] == first.sha256)
        check("provenance records application version", data_a["application_version"] == "0.1.1")

        tampered = base / "release-a" / "tampered.zip"
        tampered.write_bytes(artifact_a.read_bytes() + b"tamper")
        expect_error(
            "provenance rejects artifact checksum drift",
            lambda: release_provenance.validate_provenance(provenance_a, tampered, first.manifest),
            "artifact checksum mismatch",
        )

        missing_revision = release_provenance.build_provenance(
            distribution,
            first.manifest,
            first.artifact,
            source_revision="",
        )
        check("missing source revision is represented explicitly", missing_revision["source_revision"] == "unknown")

    print("RSD-18 release provenance/reproducibility checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
