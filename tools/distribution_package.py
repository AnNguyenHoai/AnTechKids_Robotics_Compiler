"""Assemble a relocatable RoboStudio distribution from application-owned inputs."""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from tools import runtime_preflight, runtime_resources

DISTRIBUTION_MANIFEST = "distribution-manifest.json"
SCHEMA = "antechkids.robostudio.distribution"
SCHEMA_VERSION = 1


class DistributionPackageError(RuntimeError):
    """Raised when a distribution cannot be assembled safely."""


@dataclass(frozen=True)
class DistributionInputs:
    executable: Path
    runtime_bin: Path
    runtime_platformio: Path
    runtime_resources: Path


def _copy_tree(source: Path, destination: Path, label: str) -> None:
    if not source.is_dir():
        raise DistributionPackageError(f"Missing distribution input {label}: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            if item.name.lower() == "penv":
                raise DistributionPackageError(f"Host-specific PlatformIO penv is not allowed: {item}")
            shutil.copytree(item, target, dirs_exist_ok=True)
        elif item.is_file():
            shutil.copy2(item, target)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_entries(root: Path) -> list[dict[str, object]]:
    return [
        {"path": p.relative_to(root).as_posix(), "size": p.stat().st_size, "sha256": _sha256(p)}
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != DISTRIBUTION_MANIFEST
    ]


def assemble_distribution(inputs: DistributionInputs, output: Path) -> Path:
    """Build a clean distribution and return its distribution manifest."""
    output = Path(output)
    if output.exists():
        if not output.is_dir():
            raise DistributionPackageError(f"Distribution output is not a directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    executable = Path(inputs.executable)
    if not executable.is_file():
        raise DistributionPackageError(f"Missing RoboStudio executable: {executable}")
    shutil.copy2(executable, output / executable.name)

    _copy_tree(inputs.runtime_bin, output / runtime_preflight.RUNTIME_BIN, "portable Python")
    _copy_tree(inputs.runtime_platformio, output / runtime_preflight.RUNTIME_PLATFORMIO, "PlatformIO")
    _copy_tree(inputs.runtime_resources, output / runtime_preflight.RUNTIME_RESOURCES, "runtime resources")

    # Regenerate resource metadata after copying so the manifest describes the
    # exact bytes shipped in the output rather than host input metadata.
    runtime_resources.write_resource_manifest(output / runtime_preflight.RUNTIME_RESOURCES)
    deployment_manifest = output / runtime_preflight.RUNTIME_PLATFORMIO / runtime_preflight.DEPLOYMENT_MANIFEST
    if not deployment_manifest.is_file():
        raise DistributionPackageError(f"PlatformIO deployment manifest is missing: {deployment_manifest}")

    try:
        runtime_preflight.validate_distribution(output)
    except Exception as exc:
        raise DistributionPackageError(f"Assembled distribution failed runtime preflight: {exc}") from exc

    manifest = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "application": executable.name,
        "portable": True,
        "runtime_root": "runtime",
        "files": _file_entries(output),
    }
    manifest_path = output / DISTRIBUTION_MANIFEST
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def validate_distribution_manifest(path: Path) -> dict:
    """Validate the shipped file list and SHA-256 digests.

    Content integrity is authoritative: when both the recorded size and digest
    have drifted, report the checksum mismatch rather than masking the content
    change behind the size check. A pure size-only inconsistency is still
    reported as size drift for diagnostics.
    """
    path = Path(path)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DistributionPackageError(f"Unable to load distribution manifest: {exc}") from exc
    if manifest.get("schema") != SCHEMA or manifest.get("schema_version") != SCHEMA_VERSION:
        raise DistributionPackageError("Unsupported distribution manifest schema")
    root = path.parent
    for entry in manifest.get("files", []):
        relative = Path(str(entry.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise DistributionPackageError("Distribution manifest contains an unsafe path")
        target = root / relative
        if not target.is_file():
            raise DistributionPackageError(f"Distribution file is missing: {relative.as_posix()}")

        actual_size = target.stat().st_size
        actual_sha256 = _sha256(target)
        expected_size = entry.get("size")
        expected_sha256 = entry.get("sha256")

        if actual_sha256 != expected_sha256:
            if actual_size != expected_size:
                raise DistributionPackageError(
                    f"Distribution file checksum mismatch: {relative.as_posix()} "
                    f"(size changed from {expected_size} to {actual_size})"
                )
            raise DistributionPackageError(f"Distribution file checksum mismatch: {relative.as_posix()}")
        if actual_size != expected_size:
            raise DistributionPackageError(f"Distribution file size changed: {relative.as_posix()}")
    return manifest
