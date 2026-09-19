#!/usr/bin/env python3
"""Regression gate for B2.6 release/copy-and-run contract."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import (
    copy_run_contract,
    copy_run_release,
    distribution_package,
    one_command_production_build,
    release_compatibility,
    release_package,
    runtime_integrity,
)


def _write(path: Path, data: bytes = b"x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _contract_payload(root: Path) -> dict:
    _write(root / "RoboStudio.exe", b"exe")
    (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
    return copy_run_contract.build_contract(root, application="RoboStudio.exe")


def _zip_fixture(temp: Path, *, mutate_contract=None, ready: bool = True, include_contract: bool = True) -> tuple[Path, Path]:
    root = temp / "contract-root"
    root.mkdir(parents=True)
    contract = _contract_payload(root)
    if mutate_contract is not None:
        mutate_contract(contract)

    members: dict[str, bytes] = {
        "RoboStudio.cmd": b"@echo off\r\nRoboStudio.exe\r\n",
        "RoboStudio.exe": b"exe",
        "VERSION": b"1.2.3\n",
        "runtime/bin/python.exe": b"python",
        "runtime/platformio/platforms/espressif32/platform.json": b"{}",
        "runtime/platformio/packages/tool-esptoolpy/esptool.py": b"# tool",
        "compiler/main.py": b"# compiler",
        "firmware/robot-platform/platformio.ini": b"[env:esp32dev]",
        "tools/clean_machine_physical_e2e.py": b"# acceptance",
    }
    distribution = {
        "schema": distribution_package.SCHEMA,
        "schema_version": distribution_package.SCHEMA_VERSION,
        "application": "RoboStudio.exe",
        "copy_run_contract": copy_run_contract.CONTRACT_NAME,
        "copy_run_ready": ready,
    }
    members[distribution_package.DISTRIBUTION_MANIFEST] = (json.dumps(distribution, indent=2) + "\n").encode()
    if include_contract:
        members[copy_run_contract.CONTRACT_NAME] = (json.dumps(contract, indent=2) + "\n").encode()

    artifact = temp / "RoboStudio-1.2.3-Windows.zip"
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)

    compatibility = release_compatibility.build_compatibility(
        "1.2.3",
        runtime_integrity_schema_version=runtime_integrity.SCHEMA_VERSION,
        distribution_schema_version=distribution_package.SCHEMA_VERSION,
        release_schema_version=release_package.RELEASE_SCHEMA_VERSION,
        portable_python_required=True,
        bundled_platformio_required=True,
    )
    release_manifest = {
        "schema": release_package.RELEASE_SCHEMA,
        "schema_version": release_package.RELEASE_SCHEMA_VERSION,
        "artifact": artifact.name,
        "portable": True,
        "artifact_model": distribution_package.CANONICAL_PRODUCTION_ARTIFACT_MODEL,
        "production_boundary": True,
        "application": "RoboStudio.exe",
        "application_version": "1.2.3",
        "distribution_manifest": distribution_package.DISTRIBUTION_MANIFEST,
        "compatibility": compatibility,
        "file_count": len(members),
        "files": [
            {"path": name, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            for name, payload in sorted(members.items())
        ],
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }
    manifest_path = temp / release_package.RELEASE_MANIFEST
    manifest_path.write_text(json.dumps(release_manifest, indent=2) + "\n", encoding="utf-8")
    return artifact, manifest_path


def _expect_fail(callback, contains: str) -> None:
    try:
        callback()
    except (copy_run_contract.CopyRunContractError, copy_run_release.CopyRunReleaseError) as exc:
        if contains.lower() not in str(exc).lower():
            raise AssertionError(f"Expected failure containing {contains!r}, got: {exc}") from exc
    else:
        raise AssertionError(f"Expected failure containing {contains!r}")


def test_contract_semantics() -> None:
    with tempfile.TemporaryDirectory(prefix="b2-6-contract-") as td:
        root = Path(td)
        payload = _contract_payload(root)
        result = copy_run_contract.validate_payload(payload, expected_application="RoboStudio.exe", expected_version="1.2.3")
        assert result["delivery_model"] == "copy-extract-run"
        assert result["host_requirements"]["python"] is False
        assert result["host_requirements"]["platformio"] is False
        assert result["state"]["inside_artifact_allowed"] is False
        assert result["relocation"]["copy_to_another_machine_supported"] is True

        poisoned = json.loads(json.dumps(payload))
        poisoned["host_requirements"]["python"] = True
        _expect_fail(lambda: copy_run_contract.validate_payload(poisoned), "host_requirements.python")

        absolute = json.loads(json.dumps(payload))
        absolute["runtime"]["python"] = "C:/Python/python.exe"
        _expect_fail(lambda: copy_run_contract.validate_payload(absolute), "runtime.python")


def test_release_host_path_filter_boundaries() -> None:
    # PlatformIO legitimately contains a package path segment named `home`.
    # The release manifest inventories that relative path, and it must not be
    # mistaken for a leaked absolute Linux home directory.
    relative_package_path = (
        b'{"path":"runtime/bin/Lib/site-packages/platformio/home/app.py"}'
    )
    release_package._reject_forbidden_text(relative_package_path, "distribution-manifest.json")

    for leaked in (
        b'{"cache":"/home/alice/.platformio"}',
        b'{"cache":"/Users/alice/.platformio"}',
        b'config=/home/alice/build',
    ):
        try:
            release_package._reject_forbidden_text(leaked, "fixture.json")
        except release_package.ReleasePackageError:
            pass
        else:
            raise AssertionError(f"Absolute host path must remain forbidden: {leaked!r}")


def test_release_zip_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="b2-6-zip-") as td:
        temp = Path(td)
        artifact, manifest = _zip_fixture(temp)
        report = copy_run_release.validate_release_zip(artifact, manifest)
        assert report["status"] == "PASS"
        assert report["copy_run_ready"] is True
        assert report["host_python_required"] is False
        assert report["host_platformio_required"] is False
        assert report["host_compiler_toolchain_required"] is False
        assert report["external_state_required"] is True

    with tempfile.TemporaryDirectory(prefix="b2-6-host-python-") as td:
        artifact, manifest = _zip_fixture(
            Path(td), mutate_contract=lambda payload: payload["host_requirements"].__setitem__("python", True)
        )
        _expect_fail(lambda: copy_run_release.validate_release_zip(artifact, manifest), "host_requirements.python")

    with tempfile.TemporaryDirectory(prefix="b2-6-absolute-") as td:
        artifact, manifest = _zip_fixture(
            Path(td), mutate_contract=lambda payload: payload["runtime"].__setitem__("python", "C:/host/python.exe")
        )
        _expect_fail(lambda: copy_run_release.validate_release_zip(artifact, manifest), "runtime.python")

    with tempfile.TemporaryDirectory(prefix="b2-6-missing-") as td:
        artifact, manifest = _zip_fixture(Path(td), include_contract=False)
        _expect_fail(lambda: copy_run_release.validate_release_zip(artifact, manifest), "does not inventory")

    with tempfile.TemporaryDirectory(prefix="b2-6-not-ready-") as td:
        artifact, manifest = _zip_fixture(Path(td), ready=False)
        _expect_fail(lambda: copy_run_release.validate_release_zip(artifact, manifest), "does not require")


def _minimal_one_command_inputs(root: Path) -> dict[str, Path]:
    executable = _write(root / "app" / "RoboStudio.exe", b"exe")
    runtime_bin = root / "runtime-bin"
    _write(runtime_bin / "python.exe", b"python")
    _write(runtime_bin / "Lib" / "site-packages" / "platformio" / "__init__.py", b"# pio")
    runtime_platformio = root / "runtime-platformio"
    (runtime_platformio / "platforms").mkdir(parents=True)
    (runtime_platformio / "packages").mkdir(parents=True)
    runtime_resources = root / "resources"
    runtime_resources.mkdir()
    firmware = root / "firmware"
    _write(firmware / "platformio.ini", b"[env:esp32dev]")
    _write(firmware / "wifi_config.py", b"# wifi")
    (firmware / "main").mkdir(parents=True)
    version = root / "VERSION"
    version.write_text("1.2.3\n", encoding="utf-8")
    return {
        "executable": executable,
        "runtime_bin": runtime_bin,
        "runtime_platformio": runtime_platformio,
        "runtime_resources": runtime_resources,
        "firmware": firmware,
        "version": version,
        "output": root / "out" / "production",
    }


def test_one_command_uses_b2_6_finalizer() -> None:
    with tempfile.TemporaryDirectory(prefix="b2-6-one-command-") as td:
        paths = _minimal_one_command_inputs(Path(td))
        original_assemble = one_command_production_build.production_release_assembly.assemble_release
        original_finalize = one_command_production_build.copy_run_release.finalize_assembly_result
        calls: list[str] = []
        try:
            def fake_assemble(inputs, output):
                calls.append("assemble")
                output.mkdir(parents=True, exist_ok=True)
                distribution = output / "RoboStudio"
                distribution.mkdir()
                artifact = output / "RoboStudio-1.2.3-Windows.zip"
                artifact.write_bytes(b"zip")
                return {
                    "distribution": str(distribution),
                    "artifact": str(artifact),
                    "artifact_sha256": "old",
                }

            def fake_finalize(result, *, source_revision):
                calls.append("finalize")
                assert source_revision == "deadbeef"
                updated = dict(result)
                updated["artifact_sha256"] = "final"
                updated["b2_6"] = {"status": "PASS", "copy_run_ready": True}
                return updated

            one_command_production_build.production_release_assembly.assemble_release = fake_assemble
            one_command_production_build.copy_run_release.finalize_assembly_result = fake_finalize
            result = one_command_production_build.build(
                paths["executable"],
                paths["runtime_bin"],
                paths["runtime_platformio"],
                paths["runtime_resources"],
                paths["version"],
                "deadbeef",
                paths["output"],
                paths["firmware"],
            )
        finally:
            one_command_production_build.production_release_assembly.assemble_release = original_assemble
            one_command_production_build.copy_run_release.finalize_assembly_result = original_finalize

        assert calls == ["assemble", "finalize"]
        assert result["artifact_sha256"] == "final"
        assert result["b2_6"]["copy_run_ready"] is True
        assert result["b2_6"]["canonical_release_path"] is True


def main() -> int:
    tests = [
        test_contract_semantics,
        test_release_host_path_filter_boundaries,
        test_release_zip_contract,
        test_one_command_uses_b2_6_finalizer,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print("B2.6 release/copy-and-run contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
