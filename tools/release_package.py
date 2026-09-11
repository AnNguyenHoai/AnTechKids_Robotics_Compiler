"""Build and validate a portable RoboStudio release artifact.

RSD-07 assembles a distribution directory and RSD-08 defines clean-machine
launch semantics. This module adds the release boundary: create a reproducible
ZIP artifact from an already validated distribution, reject host-specific
content, and validate the artifact without extracting it into the current
working directory.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from tools import distribution_package, release_compatibility, runtime_integrity, runtime_preflight

RELEASE_MANIFEST = "release-manifest.json"
RELEASE_SCHEMA = "antechkids.robostudio.release"
RELEASE_SCHEMA_VERSION = 1
ARTIFACT_SUFFIX = ".zip"

_FORBIDDEN_PARTS = {
    ".git",
    ".pio",
    "penv",
    "__pycache__",
}
# These markers identify host-owned installation roots.  ``site-packages`` is
# intentionally not forbidden by itself: it is a valid directory name inside a
# self-contained Python runtime and can legitimately occur in a generated
# distribution manifest. Host leakage is rejected when the host installation
# root itself is embedded in textual metadata.
_FORBIDDEN_TEXT = (
    "\\AppData\\Local\\Programs\\Python",
    "\\AppData\\Local\\pypoetry",
    "\\.platformio",
    "/home/",
    "/Users/",
)


class ReleasePackageError(RuntimeError):
    """Raised when a release artifact cannot satisfy the packaging contract."""


@dataclass(frozen=True)
class ReleaseArtifact:
    """Metadata for a validated release ZIP."""

    artifact: Path
    manifest: Path
    file_count: int
    sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(name: str) -> bool:
    path = Path(name.replace("/", "\\"))
    return not path.is_absolute() and ".." not in path.parts and not any(
        part.lower() in _FORBIDDEN_PARTS for part in path.parts
    )


def _reject_forbidden_text(data: bytes, name: str) -> None:
    if not name.lower().endswith((".json", ".txt", ".cfg", ".ini", ".toml", ".yaml", ".yml")):
        return
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return
    normalized = text.replace("\\", "/")
    for marker in _FORBIDDEN_TEXT:
        if marker.replace("\\", "/") in normalized:
            raise ReleasePackageError(f"Release contains host-specific path in {name}: {marker}")


def _archive_entries(root: Path) -> tuple[list[tuple[Path, str]], list[str]]:
    """Return file entries and explicit empty-directory entries."""
    files: list[tuple[Path, str]] = []
    directories: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative == RELEASE_MANIFEST:
            continue
        if not _safe_member(relative):
            raise ReleasePackageError(f"Release contains forbidden path: {relative}")
        if path.is_dir():
            if not any(path.iterdir()):
                directories.append(relative.rstrip("/") + "/")
            continue
        if path.is_file():
            files.append((path, relative))
    return files, directories


def build_release(distribution_root: Path, artifact: Path) -> ReleaseArtifact:
    """Validate a distribution and package it as a portable ZIP artifact."""
    root = Path(distribution_root).resolve()
    artifact = Path(artifact).resolve()
    if not root.is_dir():
        raise ReleasePackageError(f"Distribution directory not found: {root}")
    if artifact == root or root in artifact.parents:
        raise ReleasePackageError("Release artifact must not be created inside the distribution directory.")

    try:
        runtime_preflight.validate_distribution(root)
        distribution_manifest = distribution_package.validate_distribution_manifest(
            root / distribution_package.DISTRIBUTION_MANIFEST
        )
    except Exception as exc:
        raise ReleasePackageError(f"Distribution validation failed: {exc}") from exc

    entries, directories = _archive_entries(root)
    if not entries:
        raise ReleasePackageError("Distribution contains no release files")

    artifact.parent.mkdir(parents=True, exist_ok=True)
    if artifact.exists():
        artifact.unlink()

    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in directories:
            archive.writestr(relative, b"")
        for source, relative in entries:
            archive.write(source, relative)

    application_version = runtime_integrity.application_version(root)
    if application_version == "unknown":
        raise ReleasePackageError("Release distribution does not declare an application VERSION")
    try:
        compatibility = release_compatibility.build_compatibility(
            application_version,
            runtime_integrity_schema_version=runtime_integrity.SCHEMA_VERSION,
            distribution_schema_version=distribution_package.SCHEMA_VERSION,
            release_schema_version=RELEASE_SCHEMA_VERSION,
        )
    except release_compatibility.ReleaseCompatibilityError as exc:
        raise ReleasePackageError(f"Invalid release compatibility contract: {exc}") from exc

    manifest = {
        "schema": RELEASE_SCHEMA,
        "schema_version": RELEASE_SCHEMA_VERSION,
        "artifact": artifact.name,
        "portable": True,
        "application": distribution_manifest.get("application"),
        "application_version": application_version,
        "distribution_manifest": distribution_package.DISTRIBUTION_MANIFEST,
        "compatibility": compatibility,
        "file_count": len(entries),
        "files": [
            {"path": relative, "size": source.stat().st_size, "sha256": _sha256(source)}
            for source, relative in entries
        ],
        "artifact_sha256": _sha256(artifact),
    }
    manifest_path = artifact.with_name(RELEASE_MANIFEST)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return ReleaseArtifact(artifact, manifest_path, len(entries), manifest["artifact_sha256"])


def validate_release_artifact(artifact: Path, manifest: Path | None = None) -> dict:
    """Validate ZIP safety, expected files, and the release manifest."""
    artifact = Path(artifact).resolve()
    manifest_path = Path(manifest).resolve() if manifest else artifact.with_name(RELEASE_MANIFEST)
    if not artifact.is_file():
        raise ReleasePackageError(f"Release artifact not found: {artifact}")
    if not manifest_path.is_file():
        raise ReleasePackageError(f"Release manifest not found: {manifest_path}")

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleasePackageError(f"Unable to load release manifest: {exc}") from exc
    if data.get("schema") != RELEASE_SCHEMA or data.get("schema_version") != RELEASE_SCHEMA_VERSION:
        raise ReleasePackageError("Unsupported release manifest schema")

    if _sha256(artifact) != data.get("artifact_sha256"):
        raise ReleasePackageError("Release artifact checksum mismatch")

    if data.get("artifact") != artifact.name or data.get("portable") is not True:
        raise ReleasePackageError("Release manifest does not describe this portable artifact")

    try:
        compatibility = release_compatibility.read_compatibility(data)
    except release_compatibility.ReleaseCompatibilityError as exc:
        raise ReleasePackageError(f"Invalid release compatibility contract: {exc}") from exc

    if data.get("application_version") != compatibility.application_version:
        raise ReleasePackageError("Release manifest application version disagrees with compatibility contract")

    if compatibility.runtime_integrity_schema_version != runtime_integrity.SCHEMA_VERSION:
        raise ReleasePackageError(
            "Release is incompatible with runtime integrity schema "
            f"{runtime_integrity.SCHEMA_VERSION}"
        )
    if compatibility.distribution_schema_version != distribution_package.SCHEMA_VERSION:
        raise ReleasePackageError(
            "Release is incompatible with distribution schema "
            f"{distribution_package.SCHEMA_VERSION}"
        )
    if compatibility.release_schema_version != RELEASE_SCHEMA_VERSION:
        raise ReleasePackageError(
            f"Release is incompatible with release schema {RELEASE_SCHEMA_VERSION}"
        )

    expected = {str(item.get("path")): item for item in data.get("files", [])}
    try:
        with zipfile.ZipFile(artifact, "r") as archive:
            members = archive.infolist()
            names = [item.filename for item in members]
            if len(names) != len(set(names)):
                raise ReleasePackageError("Release artifact contains duplicate paths")
            file_members = [item for item in members if not item.is_dir()]
            file_names = [item.filename for item in file_members]
            if set(file_names) != set(expected):
                raise ReleasePackageError("Release artifact file list does not match release manifest")
            for item in members:
                if not _safe_member(item.filename.rstrip("/")):
                    raise ReleasePackageError(f"Release artifact contains unsafe path: {item.filename}")
                if item.is_dir():
                    continue
                payload = archive.read(item)
                _reject_forbidden_text(payload, item.filename)
                entry = expected[item.filename]
                if len(payload) != entry.get("size"):
                    raise ReleasePackageError(f"Release file size changed: {item.filename}")
                if hashlib.sha256(payload).hexdigest() != entry.get("sha256"):
                    raise ReleasePackageError(f"Release file checksum mismatch: {item.filename}")
    except zipfile.BadZipFile as exc:
        raise ReleasePackageError(f"Invalid release ZIP: {artifact}") from exc

    return data


def validate_release_compatibility(manifest: dict, **kwargs) -> release_compatibility.Compatibility:
    """Public compatibility validation API for launch/update gates."""
    try:
        return release_compatibility.validate_compatibility(manifest, **kwargs)
    except release_compatibility.ReleaseCompatibilityError as exc:
        raise ReleasePackageError(str(exc)) from exc


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build and validate a portable RoboStudio release ZIP")
    parser.add_argument("--distribution", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.validate:
        validate_release_artifact(args.output)
        print(f"Release artifact valid: {args.output.resolve()}")
        return 0

    result = build_release(args.distribution, args.output)
    print(f"Release artifact: {result.artifact}")
    print(f"Files packaged: {result.file_count}")
    print(f"Manifest: {result.manifest}")
    print(f"SHA-256: {result.sha256}")
    return 0
