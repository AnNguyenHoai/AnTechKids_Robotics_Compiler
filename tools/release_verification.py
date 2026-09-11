"""Independent integrity verification for portable RoboStudio releases.

RSD-19 adds a release-side verification boundary. Verification operates on
an already-built ZIP without extracting it and does not depend on the current
working directory, source tree, or host runtime.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from tools import release_package, release_provenance

VERIFICATION_SCHEMA = "antechkids.robostudio.release-verification"
VERIFICATION_SCHEMA_VERSION = 1


class ReleaseVerificationError(RuntimeError):
    """Raised when a release artifact fails integrity verification."""


@dataclass(frozen=True)
class VerificationReport:
    artifact: Path
    file_count: int
    artifact_sha256: str
    provenance_validated: bool


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(name: str) -> bool:
    if not name or "\\" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and all(part not in ("", ".") for part in path.parts)


def _load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseVerificationError(f"Unable to load {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ReleaseVerificationError(f"Invalid {label}: expected JSON object")
    return value


def _manifest_entries(manifest: dict) -> dict[str, dict]:
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ReleaseVerificationError("Release manifest has no file inventory")
    result: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ReleaseVerificationError("Release manifest contains an invalid file entry")
        name = entry["path"]
        if not _safe_member(name):
            raise ReleaseVerificationError(f"Release manifest contains unsafe path: {name}")
        if name in result:
            raise ReleaseVerificationError(f"Release manifest contains duplicate path: {name}")
        try:
            size = int(entry["size"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ReleaseVerificationError(f"Release manifest has invalid size: {name}") from exc
        digest = str(entry.get("sha256", ""))
        if size < 0 or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest.lower()):
            raise ReleaseVerificationError(f"Release manifest has invalid checksum entry: {name}")
        result[name] = {"path": name, "size": size, "sha256": digest.lower()}
    return result


def verify_release_artifact(artifact: Path, release_manifest: Path | None = None, provenance: Path | None = None) -> VerificationReport:
    """Verify a complete release ZIP and its optional provenance sidecar."""
    artifact = Path(artifact).resolve()
    manifest_path = Path(release_manifest).resolve() if release_manifest else artifact.with_name(release_package.RELEASE_MANIFEST)
    provenance_path = Path(provenance).resolve() if provenance else artifact.with_name(release_provenance.PROVENANCE_MANIFEST)

    if not artifact.is_file():
        raise ReleaseVerificationError(f"Release artifact not found: {artifact}")
    if not manifest_path.is_file():
        raise ReleaseVerificationError(f"Release manifest not found: {manifest_path}")

    manifest = _load_json(manifest_path, "release manifest")
    if manifest.get("schema") != release_package.RELEASE_SCHEMA or manifest.get("schema_version") != release_package.RELEASE_SCHEMA_VERSION:
        raise ReleaseVerificationError("Unsupported release manifest schema")
    if manifest.get("portable") is not True:
        raise ReleaseVerificationError("Release artifact is not declared portable")

    entries = _manifest_entries(manifest)
    expected_artifact_sha = str(manifest.get("artifact_sha256", "")).lower()
    if len(expected_artifact_sha) != 64:
        raise ReleaseVerificationError("Release manifest has an invalid artifact checksum")
    # Verify content identity before filename identity so a renamed/tampered
    # artifact reports the actual integrity failure deterministically.
    actual_artifact_sha = _sha256(artifact)
    if actual_artifact_sha != expected_artifact_sha:
        raise ReleaseVerificationError("Release artifact checksum mismatch")
    if manifest.get("artifact") != artifact.name:
        raise ReleaseVerificationError("Release manifest does not describe this artifact")

    try:
        with zipfile.ZipFile(artifact, "r") as archive:
            bad = archive.testzip()
            if bad is not None:
                raise ReleaseVerificationError(f"Release artifact has corrupt ZIP member: {bad}")
            members = archive.infolist()
            names = [item.filename for item in members]
            if len(names) != len(set(names)):
                raise ReleaseVerificationError("Release artifact contains duplicate paths")
            for item in members:
                name = item.filename.rstrip("/") if item.is_dir() else item.filename
                if not _safe_member(name):
                    raise ReleaseVerificationError(f"Release artifact contains unsafe path: {item.filename}")
            file_members = [item for item in members if not item.is_dir()]
            actual_names = {item.filename for item in file_members}
            expected_names = set(entries)
            if actual_names != expected_names:
                missing = sorted(expected_names - actual_names)
                extra = sorted(actual_names - expected_names)
                if missing:
                    raise ReleaseVerificationError(f"Release artifact is missing file: {missing[0]}")
                raise ReleaseVerificationError(f"Release artifact contains unexpected file: {extra[0]}")
            for item in file_members:
                payload = archive.read(item)
                expected = entries[item.filename]
                if len(payload) != expected["size"]:
                    raise ReleaseVerificationError(f"Release file size mismatch: {item.filename}")
                digest = hashlib.sha256(payload).hexdigest()
                if digest != expected["sha256"]:
                    raise ReleaseVerificationError(f"Release file checksum mismatch: {item.filename}")
                try:
                    release_package._reject_forbidden_text(payload, item.filename)
                except release_package.ReleasePackageError as exc:
                    raise ReleaseVerificationError(str(exc)) from exc
    except zipfile.BadZipFile as exc:
        raise ReleaseVerificationError(f"Invalid release ZIP: {artifact}") from exc

    provenance_validated = False
    if provenance_path.is_file():
        try:
            release_provenance.validate_provenance(provenance_path, artifact, manifest_path)
        except ValueError as exc:
            raise ReleaseVerificationError(f"Release provenance verification failed: {exc}") from exc
        provenance_validated = True

    return VerificationReport(artifact=artifact, file_count=len(entries), artifact_sha256=actual_artifact_sha, provenance_validated=provenance_validated)


def verify_or_raise(artifact: Path, release_manifest: Path | None = None, provenance: Path | None = None) -> VerificationReport:
    return verify_release_artifact(artifact, release_manifest, provenance)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Verify a portable RoboStudio release artifact")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--provenance", type=Path)
    args = parser.parse_args()
    report = verify_release_artifact(args.artifact, args.manifest, args.provenance)
    print("RoboStudio release verification: PASS")
    print(f"Artifact: {report.artifact}")
    print(f"Files: {report.file_count}")
    print(f"SHA-256: {report.artifact_sha256}")
    print(f"Provenance: {'validated' if report.provenance_validated else 'not supplied'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
