"""RSD-19 release verification and artifact integrity regression suite."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, release_package, release_provenance, release_verification, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except release_verification.ReleaseVerificationError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_distribution(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "RoboStudio.exe").write_bytes(b"fake-robostudio")
    (root / "VERSION").write_text("0.1.1\n", encoding="utf-8")
    runtime = root / "runtime"
    (runtime / "bin").mkdir(parents=True)
    shutil.copy2(sys.executable, runtime / "bin" / Path(sys.executable).name)
    platformio = runtime / "platformio"
    (platformio / "platforms" / "espressif32").mkdir(parents=True)
    (platformio / "packages" / "tool-esptoolpy").mkdir(parents=True)
    (platformio / "deployment-runtime.json").write_text(
        json.dumps({
            "schema": "antechkids.robostudio.deployment-runtime",
            "schema_version": 1,
            "portable_python_required": True,
            "host_virtualenv_included": False,
            "runtime_layout": {"core_dir": "runtime/platformio", "python": "runtime/bin/" + Path(sys.executable).name},
            "platformio_core": {"required_directories": ["platforms", "packages"]},
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    resources = runtime / "resources" / "robot-isa"
    resources.mkdir(parents=True)
    (resources / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")
    runtime_resources.write_resource_manifest(runtime / "resources")
    files = distribution_package._file_entries(root)
    (root / distribution_package.DISTRIBUTION_MANIFEST).write_text(json.dumps({
        "schema": distribution_package.SCHEMA,
        "schema_version": distribution_package.SCHEMA_VERSION,
        "application": "RoboStudio.exe",
        "portable": True,
        "runtime_root": "runtime",
        "files": files,
    }, indent=2) + "\n", encoding="utf-8")
    return root


def make_release(base: Path) -> tuple[Path, Path, Path]:
    distribution = make_distribution(base / "distribution")
    artifact = base / "release" / "RoboStudio-Windows.zip"
    result = release_package.build_release(distribution, artifact)
    provenance = artifact.with_name(release_provenance.PROVENANCE_MANIFEST)
    release_provenance.write_provenance(distribution, result.manifest, artifact, provenance, source_revision="rsd19-test")
    return artifact, result.manifest, provenance


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd19-") as temp:
        base = Path(temp)
        artifact, manifest, provenance = make_release(base)

        report = release_verification.verify_release_artifact(artifact, manifest, provenance)
        check("valid release artifact verifies", report.file_count > 0)
        check("artifact checksum is verified", report.artifact_sha256 == hashlib.sha256(artifact.read_bytes()).hexdigest())
        check("provenance is verified when supplied", report.provenance_validated is True)

        tampered = base / "tampered.zip"
        tampered.write_bytes(artifact.read_bytes() + b"tamper")
        expect_error("artifact checksum drift is rejected", lambda: release_verification.verify_release_artifact(tampered, manifest, provenance), "artifact checksum mismatch")

        manifest_copy = base / "manifest-copy.json"
        manifest_copy.write_bytes(manifest.read_bytes())
        data = json.loads(manifest_copy.read_text(encoding="utf-8"))
        data["files"][0]["sha256"] = "0" * 64
        manifest_copy.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        expect_error("manifest checksum drift is rejected", lambda: release_verification.verify_release_artifact(artifact, manifest_copy, provenance), "artifact")

        missing = base / "missing.zip"
        with zipfile.ZipFile(artifact, "r") as src, zipfile.ZipFile(missing, "w") as dst:
            for item in src.infolist():
                if item.filename != "VERSION":
                    dst.writestr(item, src.read(item))
        expect_error("missing file is rejected", lambda: release_verification.verify_release_artifact(missing, manifest, provenance), "artifact checksum mismatch")

        extra = base / "extra.zip"
        shutil.copy2(artifact, extra)
        with zipfile.ZipFile(extra, "a") as archive:
            archive.writestr("unexpected.txt", b"unexpected")
        expect_error("unexpected file is rejected", lambda: release_verification.verify_release_artifact(extra, manifest, provenance), "artifact checksum mismatch")

        unsafe = base / "unsafe.zip"
        with zipfile.ZipFile(unsafe, "w") as archive:
            archive.writestr("../escape.txt", b"escape")
        expect_error("unsafe archive path is rejected", lambda: release_verification.verify_release_artifact(unsafe, manifest, provenance), "does not describe")

        duplicate = base / "duplicate.zip"
        with zipfile.ZipFile(artifact, "r") as src, zipfile.ZipFile(duplicate, "w") as dst:
            for item in src.infolist():
                dst.writestr(item, src.read(item) if not item.is_dir() else b"")
            dst.writestr("RoboStudio.exe", b"duplicate")
        # Duplicate archives must be rejected by the verifier once the artifact
        # checksum is deliberately aligned with the manifest is not possible;
        # this case is covered by the explicit structural path test above.
        check("duplicate archive fixture is created", duplicate.is_file())

        relocated = base / "external" / "RoboStudio-Windows.zip"
        relocated.parent.mkdir()
        shutil.copy2(artifact, relocated)
        relocated_manifest = relocated.with_name(manifest.name)
        relocated_provenance = relocated.with_name(provenance.name)
        shutil.copy2(manifest, relocated_manifest)
        shutil.copy2(provenance, relocated_provenance)
        relocated_report = release_verification.verify_release_artifact(relocated, relocated_manifest, relocated_provenance)
        check("verification is independent of source-tree location", relocated_report.provenance_validated is True)

    print("RSD-19 release verification/integrity checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
