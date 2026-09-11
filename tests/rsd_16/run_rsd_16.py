"""RSD-16 clean-machine release acceptance regression suite."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, release_acceptance, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except release_acceptance.ReleaseAcceptanceError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def _copy_portable_python(runtime_root: Path) -> None:
    """Stage a runnable interpreter without copying host virtualenv metadata."""
    runtime_bin = runtime_root / "bin"
    runtime_bin.mkdir(parents=True, exist_ok=True)
    python_name = "python.exe" if os.name == "nt" else "python"
    source_python = Path(sys.executable).resolve()
    shutil.copy2(source_python, runtime_bin / python_name)

    if os.name != "nt":
        return

    source_root = Path(sys.base_prefix).resolve()
    for source in sorted(source_root.glob("python*.dll")):
        shutil.copy2(source, runtime_bin / source.name)

    source_lib = source_root / "Lib"
    if source_lib.is_dir():
        shutil.copytree(
            source_lib,
            runtime_root / "Lib",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )

    source_dlls = source_root / "DLLs"
    if source_dlls.is_dir():
        shutil.copytree(
            source_dlls,
            runtime_root / "DLLs",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )


def _make_distribution(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "RoboStudio.exe").write_bytes(b"fake-robostudio")
    (root / "VERSION").write_text("0.1.1\n", encoding="utf-8")

    runtime = root / "runtime"
    _copy_portable_python(runtime)

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
                    "python": "runtime/bin/python.exe" if os.name == "nt" else "runtime/bin/python",
                },
                "platformio_core": {"required_directories": ["platforms", "packages"]},
            },
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


def _tamper_artifact(source: Path, destination: Path) -> None:
    """Copy a valid ZIP and alter payload bytes while retaining its manifest."""
    with zipfile.ZipFile(source, "r") as archive:
        entries = [(info.filename, archive.read(info)) for info in archive.infolist()]
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        changed = False
        for name, payload in entries:
            if not changed and name == "RoboStudio.exe":
                payload += b"tampered"
                changed = True
            archive.writestr(name, payload)
    if not changed:
        raise AssertionError("fixture did not contain application executable")


def main() -> int:
    original_env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd16-test-") as temp:
        base = Path(temp)
        distribution = _make_distribution(base / "distribution")
        artifact = base / "release" / "RoboStudio-Windows.zip"
        result = __import__("tools.release_package", fromlist=["build_release"]).build_release(
            distribution, artifact
        )

        hostile = dict(original_env)
        hostile.update(
            {
                "PATH": r"C:\HostOnly\bin",
                "PYTHONHOME": r"C:\HostPython",
                "PYTHONPATH": r"C:\HostProject",
                "VIRTUAL_ENV": r"C:\HostVenv",
                "PIOHOME_DIR": r"C:\HostPlatformIO",
                "PLATFORMIO_CORE_DIR": r"C:\HostPlatformIO",
                "PLATFORMIO_PLATFORMS_DIR": r"C:\HostPlatforms",
                "PLATFORMIO_PACKAGES_DIR": r"C:\HostPackages",
            }
        )

        report = release_acceptance.accept_release(artifact, base_env=hostile)
        check("clean-machine acceptance succeeds", report.execution_returncode == 0)
        check("release application identity is preserved", report.application == "RoboStudio.exe")
        check("release version is preserved", report.application_version == "0.1.1")
        check("relocation is verified", report.relocated_root.name == "RelocatedRoboStudio")
        check("external working directory is verified", report.external_cwd.name == "ExternalWorkspace")
        check("portable executable is verified", report.executable_verified)
        check("runtime environment is verified", report.environment_verified)
        check("artifact checksum is recorded", len(report.artifact_sha256) == hashlib.sha256().digest_size * 2)

        serialized = release_acceptance.report_to_dict(report)
        check("acceptance report has schema", serialized["schema"] == release_acceptance.SCHEMA)
        check("acceptance report has schema version", serialized["schema_version"] == 1)
        check("acceptance report is machine-readable", json.loads(json.dumps(serialized))["application"] == "RoboStudio.exe")

        tampered = base / "release" / "tampered.zip"
        _tamper_artifact(artifact, tampered)
        expect_error(
            "tampered release is rejected before runtime execution",
            lambda: release_acceptance.accept_release(tampered),
            "checksum mismatch",
        )

        missing = base / "missing.zip"
        expect_error(
            "missing release artifact is rejected",
            lambda: release_acceptance.accept_release(missing),
            "not found",
        )

    check("acceptance restores caller environment", os.environ == original_env)
    print("RSD-16 clean-machine release acceptance checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
