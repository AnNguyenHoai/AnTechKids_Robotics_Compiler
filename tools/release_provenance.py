"""Release provenance and reproducibility support for RoboStudio artifacts.

RSD-18 records deterministic release inputs and makes the ZIP byte stream
independent of source-file mtimes and filesystem traversal order. Provenance is
kept as a sidecar manifest so the release ZIP remains compatible with the
existing RSD-09/RSD-16 artifact contract.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

SCHEMA = "antechkids.robostudio.release-provenance"
SCHEMA_VERSION = 1
PROVENANCE_MANIFEST = "release-provenance.json"
SOURCE_REVISION_ENV = "RSD_SOURCE_REVISION"
UNKNOWN_REVISION = "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_file_inventory(root: Path, *, exclude: Iterable[str] = ()) -> list[dict[str, object]]:
    """Return a stable path/size/SHA-256 inventory rooted at ``root``."""
    root = Path(root).resolve()
    excluded = {str(item).replace("\\", "/") for item in exclude}
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        entries.append({"path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)})
    return entries


def _revision_from_environment() -> str:
    value = os.environ.get(SOURCE_REVISION_ENV, "").strip()
    return value or UNKNOWN_REVISION


def build_provenance(
    distribution_root: Path,
    release_manifest: Path,
    artifact: Path,
    *,
    source_revision: str | None = None,
) -> dict[str, object]:
    """Build a deterministic provenance record for a validated release."""
    distribution_root = Path(distribution_root).resolve()
    release_manifest = Path(release_manifest).resolve()
    artifact = Path(artifact).resolve()
    if not distribution_root.is_dir():
        raise ValueError(f"Distribution directory not found: {distribution_root}")
    if not release_manifest.is_file():
        raise ValueError(f"Release manifest not found: {release_manifest}")
    if not artifact.is_file():
        raise ValueError(f"Release artifact not found: {artifact}")

    manifest = json.loads(release_manifest.read_text(encoding="utf-8"))
    revision = (source_revision or _revision_from_environment()).strip()
    if not revision:
        revision = UNKNOWN_REVISION

    files = manifest.get("files", [])
    normalized_files = [
        {
            "path": str(item["path"]),
            "size": int(item["size"]),
            "sha256": str(item["sha256"]),
        }
        for item in files
    ]
    normalized_files.sort(key=lambda item: item["path"])

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "portable": True,
        "artifact": artifact.name,
        "artifact_sha256": sha256_file(artifact),
        "release_manifest_sha256": sha256_file(release_manifest),
        "distribution_manifest_sha256": sha256_file(
            distribution_root / "distribution-manifest.json"
        ),
        "source_revision": revision,
        "application": manifest.get("application"),
        "application_version": manifest.get("application_version"),
        "file_count": len(normalized_files),
        "files": normalized_files,
        "reproducibility": {
            "deterministic_zip": True,
            "zip_timestamp": "1980-01-01T00:00:00",
            "compression": "deflate",
            "compression_level": 9,
            "path_order": "lexicographic-posix",
        },
    }


def write_provenance(
    distribution_root: Path,
    release_manifest: Path,
    artifact: Path,
    output: Path,
    *,
    source_revision: str | None = None,
) -> Path:
    """Write the release provenance sidecar without embedding host paths."""
    provenance = build_provenance(
        distribution_root,
        release_manifest,
        artifact,
        source_revision=source_revision,
    )
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json(provenance))
    return output


def validate_provenance(path: Path, artifact: Path, release_manifest: Path) -> dict[str, object]:
    """Validate a provenance sidecar against the immutable release artifact."""
    path = Path(path).resolve()
    artifact = Path(artifact).resolve()
    release_manifest = Path(release_manifest).resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to load release provenance: {path}") from exc
    if data.get("schema") != SCHEMA or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported release provenance schema")
    if data.get("artifact") != artifact.name:
        raise ValueError("Release provenance artifact name mismatch")
    if data.get("artifact_sha256") != sha256_file(artifact):
        raise ValueError("Release provenance artifact checksum mismatch")
    if data.get("release_manifest_sha256") != sha256_file(release_manifest):
        raise ValueError("Release provenance release-manifest checksum mismatch")
    if data.get("source_revision") in (None, ""):
        raise ValueError("Release provenance has no source revision")
    if data.get("reproducibility", {}).get("deterministic_zip") is not True:
        raise ValueError("Release provenance does not declare deterministic packaging")
    return data
