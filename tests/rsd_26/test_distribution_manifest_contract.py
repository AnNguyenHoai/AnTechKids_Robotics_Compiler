from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools import distribution_package


def _write_manifest(root: Path, entries: list[dict[str, object]], *, production: bool = False) -> Path:
    manifest = {
        "schema": distribution_package.SCHEMA,
        "schema_version": distribution_package.SCHEMA_VERSION,
        "application": "RoboStudio.exe",
        "portable": True,
        "artifact_model": distribution_package.CANONICAL_PRODUCTION_ARTIFACT_MODEL,
        "runtime_root": "runtime",
        "production_boundary": production,
        "files": entries,
    }
    path = root / distribution_package.DISTRIBUTION_MANIFEST
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def _entry(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    data = path.read_bytes()
    return {
        "path": relative,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def test_distribution_manifest_accepts_exact_fileset(tmp_path: Path):
    (tmp_path / "RoboStudio.exe").write_bytes(b"app")
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    manifest = _write_manifest(
        tmp_path,
        [_entry(tmp_path, "RoboStudio.exe"), _entry(tmp_path, "VERSION")],
    )

    result = distribution_package.validate_distribution_manifest(manifest)

    assert result["files"]


def test_distribution_manifest_rejects_unexpected_file(tmp_path: Path):
    (tmp_path / "RoboStudio.exe").write_bytes(b"app")
    manifest = _write_manifest(tmp_path, [_entry(tmp_path, "RoboStudio.exe")])
    (tmp_path / "unexpected.dll").write_bytes(b"unexpected")

    with pytest.raises(
        distribution_package.DistributionPackageError,
        match=r"unexpected=unexpected\.dll",
    ):
        distribution_package.validate_distribution_manifest(manifest)


def test_distribution_manifest_rejects_missing_manifest_entry(tmp_path: Path):
    (tmp_path / "RoboStudio.exe").write_bytes(b"app")
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    manifest = _write_manifest(
        tmp_path,
        [_entry(tmp_path, "RoboStudio.exe"), _entry(tmp_path, "VERSION")],
    )
    (tmp_path / "VERSION").unlink()

    with pytest.raises(
        distribution_package.DistributionPackageError,
        match=r"Distribution file is missing: VERSION",
    ):
        distribution_package.validate_distribution_manifest(manifest)


def test_distribution_manifest_rejects_duplicate_path(tmp_path: Path):
    (tmp_path / "RoboStudio.exe").write_bytes(b"app")
    entry = _entry(tmp_path, "RoboStudio.exe")
    manifest = _write_manifest(tmp_path, [entry, dict(entry)])

    with pytest.raises(
        distribution_package.DistributionPackageError,
        match=r"duplicate file path: RoboStudio\.exe",
    ):
        distribution_package.validate_distribution_manifest(manifest)


def test_production_distribution_uses_canonical_artifact_model(tmp_path: Path, monkeypatch):
    from tools import production_runtime_closure

    executable = tmp_path / "inputs" / "RoboStudio.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"app")
    resources = tmp_path / "inputs" / "resources"
    resources.mkdir()
    (resources / "resource.txt").write_text("resource\n", encoding="utf-8")

    runtime_bin = tmp_path / "inputs" / "runtime-bin"
    (runtime_bin / "Lib" / "site-packages" / "platformio").mkdir(parents=True)
    (runtime_bin / "python.exe").write_bytes(b"python")
    (runtime_bin / "Lib" / "site-packages" / "platformio" / "__init__.py").write_text("", encoding="utf-8")

    runtime_platformio = tmp_path / "inputs" / "runtime-platformio"
    (runtime_platformio / "platforms").mkdir(parents=True)
    (runtime_platformio / "packages").mkdir(parents=True)
    (runtime_platformio / "deployment-runtime.json").write_text("{}\n", encoding="utf-8")

    compiler = tmp_path / "inputs" / "compiler"
    (compiler / "compiler").mkdir(parents=True)
    (compiler / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (compiler / "robostudio_bridge.py").write_text("bridge\n", encoding="utf-8")

    firmware = tmp_path / "inputs" / "firmware"
    (firmware / "main").mkdir(parents=True)
    (firmware / "platformio.ini").write_text("[platformio]\n", encoding="utf-8")
    (firmware / "wifi_config.py").write_text("config = {}\n", encoding="utf-8")

    monkeypatch.setattr(
        production_runtime_closure,
        "validate_distribution",
        lambda root: None,
    )
    monkeypatch.setattr(
        distribution_package.production_artifact_boundary,
        "validate_distribution_root",
        lambda root: {"status": "PASS"},
    )
    monkeypatch.setattr(
        distribution_package.production_artifact_boundary,
        "write_boundary_manifest",
        lambda root: root / distribution_package.production_artifact_boundary.BOUNDARY_MANIFEST,
    )

    manifest_path = distribution_package.assemble_distribution(
        distribution_package.DistributionInputs(
            executable=executable,
            runtime_resources=resources,
            runtime_bin=runtime_bin,
            runtime_platformio=runtime_platformio,
            production_boundary=True,
            compiler_root=compiler,
            firmware_root=firmware,
        ),
        tmp_path / "distribution",
    )

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["artifact_model"] == distribution_package.CANONICAL_PRODUCTION_ARTIFACT_MODEL
