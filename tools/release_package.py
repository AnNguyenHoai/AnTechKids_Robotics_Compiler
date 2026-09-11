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

from tools import distribution_package, runtime_preflight

RELEASE_MANIFEST = "release-manifest.json"
RELEASE_SCHEMA = "antechkids.robostudio.release"
RELEASE_SCHEMA_VERSION = 1
ARTIFACT_SUFFIX = ".zip"

# These patterns identify accidental developer-machine state. They are checked
# against both archive paths and textual manifest content.
_FORBIDDEN_PARTS = {
    ".git",
    ".pio",
    "penv",
    "__pycache__",
}
_FORBIDDEN_TEXT = (
    "\\AppData\\Local\\Programs\\Python",
    "\\AppData\\Local\\pypoetry",
    "\\.platformio",
    "site-packages",
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


def _archive_entries(root: Path) -> list[tuple[Path, str]]:
    entries: list[tuple[Path, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == RELEASE_MANIFEST:
            continue
        if not _safe_member(relative):
            raise ReleasePackageError(f"Release contains forbidden path: {relative}")
        entries.append((path, relative))
    return entries


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

    entries = _archive_entries(root)
    if not entries:
        raise ReleasePackageError("Distribution contains no release files")

    artifact.parent.mkdir(parents=True, exist_ok=True)
    if artifact.exists():
        artifact.unlink()

    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, relative in entries:
            archive.write(source, relative)

    manifest = {
        "schema": RELEASE_SCHEMA,
        "schema_version": RELEASE_SCHEMA_VERSION,
        "artifact": artifact.name,
        "portable": True,
        "application": distribution_manifest.get("application"),
        "distribution_manifest": distribution_package.DISTRIBUTION_MANIFEST,
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
    if data.get("artifact") != artifact.name or data.get("portable") is not True:
        raise ReleasePackageError("Release manifest does not describe this portable artifact")
    if _sha256(artifact) != data.get("artifact_sha256"):
        raise ReleasePackageError("Release artifact checksum mismatch")

    expected = {str(item.get("path")): item for item in data.get("files", [])}
    try:
        with zipfile.ZipFile(artifact, "r") as archive:
            members = archive.infolist()
            names = [item.filename for item in members]
            if len(names) != len(set(names)):
                raise ReleasePackageError("Release artifact contains duplicate paths")
            if set(names) != set(expected):
                raise ReleasePackageError("Release artifact file list does not match release manifest")
            for item in members:
                if not _safe_member(item.filename):
                    raise ReleasePackageError(f"Release artifact contains unsafe path: {item.filename}")
                if item.is_dir():
                    raise ReleasePackageError(f"Release artifact contains directory entry: {item.filename}")
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


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build a portable RoboStudio release ZIP")
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


if __name__ == "__main__":
    raise SystemExit(main())
