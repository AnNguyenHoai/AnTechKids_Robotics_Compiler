"""Integrity and version-lock validation for the packaged RoboStudio runtime.

RSD-10 establishes a deterministic runtime identity.  The manifest records the
RoboStudio application version and cryptographic fingerprints for the runtime
components that must travel with the application.  Validation is intentionally
filesystem-based and never consults PATH or the host PlatformIO installation.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

SCHEMA = "antechkids.robostudio.runtime-integrity"
SCHEMA_VERSION = 1
MANIFEST_NAME = "runtime-integrity.json"

APPLICATION_VERSION_FILE = "VERSION"

# Runtime boundaries are deliberately explicit.  A new runtime dependency must
# be added here rather than being silently accepted from the host machine.
COMPONENTS: tuple[tuple[str, Path, str], ...] = (
    ("portable_python", Path("runtime/bin"), "directory"),
    ("platformio_core", Path("runtime/platformio"), "directory"),
    ("platformio_platforms", Path("runtime/platformio/platforms"), "directory"),
    ("platformio_packages", Path("runtime/platformio/packages"), "directory"),
    ("runtime_resources", Path("runtime/resources"), "directory"),
)


class RuntimeIntegrityError(RuntimeError):
    """Raised when a packaged runtime is incomplete or has drifted."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_safe(path: str) -> Path:
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeIntegrityError(f"Runtime manifest contains unsafe path: {path}")
    return relative


def _component_entries(root: Path, component_root: Path) -> list[dict[str, object]]:
    base = root / component_root
    if not base.is_dir():
        raise RuntimeIntegrityError(f"Missing runtime component: {component_root.as_posix()}")
    entries: list[dict[str, object]] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    if not entries:
        raise RuntimeIntegrityError(
            f"Runtime component contains no files: {component_root.as_posix()}"
        )
    return entries


def _component_fingerprint(entries: list[dict[str, object]]) -> str:
    """Hash the canonical file list so directory identity is deterministic."""
    canonical = "\n".join(
        f"{item['path']}\t{item['size']}\t{item['sha256']}"
        for item in entries
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def application_version(root: Path) -> str:
    """Read the repository/application version when it is shipped with root."""
    path = root / APPLICATION_VERSION_FILE
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    if not value:
        return "unknown"
    return value


def build_runtime_manifest(root: Path) -> dict[str, object]:
    """Create an integrity manifest from an application-owned runtime."""
    root = Path(root).expanduser()
    if not root.is_dir():
        raise RuntimeIntegrityError(f"RoboStudio application root does not exist: {root}")

    components: dict[str, object] = {}
    for name, relative, kind in COMPONENTS:
        entries = _component_entries(root, relative)
        components[name] = {
            "path": relative.as_posix(),
            "kind": kind,
            "file_count": len(entries),
            "sha256": _component_fingerprint(entries),
            "files": entries,
        }

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "application_version": application_version(root),
        "portable": True,
        "components": components,
    }


def write_runtime_manifest(root: Path) -> Path:
    """Write the authoritative runtime integrity manifest."""
    root = Path(root).expanduser()
    runtime = root / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    path = runtime / MANIFEST_NAME
    manifest = build_runtime_manifest(root)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def _validate_component(root: Path, name: str, descriptor: dict[str, object]) -> None:
    declared_path = _relative_safe(str(descriptor.get("path", "")))
    entries = descriptor.get("files")
    if not isinstance(entries, list) or not entries:
        raise RuntimeIntegrityError(f"Runtime integrity manifest has no files for {name}")

    actual = _component_entries(root, declared_path)
    expected = {
        str(item.get("path")): item
        for item in entries
        if isinstance(item, dict)
    }
    actual_map = {str(item["path"]): item for item in actual}
    if set(actual_map) != set(expected):
        raise RuntimeIntegrityError(f"Runtime component file list changed: {name}")

    for relative, expected_item in expected.items():
        _relative_safe(relative)
        actual_item = actual_map[relative]
        if actual_item["sha256"] != expected_item.get("sha256"):
            raise RuntimeIntegrityError(
                f"Runtime component checksum mismatch: {name}: {relative}"
            )
        if actual_item["size"] != expected_item.get("size"):
            raise RuntimeIntegrityError(
                f"Runtime component size changed: {name}: {relative}"
            )

    expected_fingerprint = str(descriptor.get("sha256", ""))
    actual_fingerprint = _component_fingerprint(actual)
    if actual_fingerprint != expected_fingerprint:
        raise RuntimeIntegrityError(f"Runtime component fingerprint mismatch: {name}")
    if descriptor.get("file_count") != len(actual):
        raise RuntimeIntegrityError(f"Runtime component file count changed: {name}")


def validate_runtime_manifest(path: Path) -> dict[str, object]:
    """Validate runtime contents against an integrity/version-lock manifest."""
    path = Path(path).expanduser()
    if not path.is_file():
        raise RuntimeIntegrityError(f"Runtime integrity manifest not found: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeIntegrityError(f"Unable to load runtime integrity manifest: {exc}") from exc

    if manifest.get("schema") != SCHEMA or manifest.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeIntegrityError("Unsupported runtime integrity manifest schema")
    if manifest.get("portable") is not True:
        raise RuntimeIntegrityError("Runtime integrity manifest must describe a portable runtime")

    root = path.parent.parent
    expected_version = str(manifest.get("application_version", "unknown"))
    actual_version = application_version(root)
    if expected_version != actual_version:
        raise RuntimeIntegrityError(
            f"RoboStudio application version changed: expected {expected_version}, got {actual_version}"
        )

    components = manifest.get("components")
    if not isinstance(components, dict):
        raise RuntimeIntegrityError("Runtime integrity manifest has no components")
    for name, descriptor in components.items():
        if not isinstance(descriptor, dict):
            raise RuntimeIntegrityError(f"Invalid runtime component descriptor: {name}")
        _validate_component(root, str(name), descriptor)

    declared_names = set(components)
    required_names = {item[0] for item in COMPONENTS}
    missing = sorted(required_names - declared_names)
    if missing:
        raise RuntimeIntegrityError(
            f"Runtime integrity manifest is missing components: {', '.join(missing)}"
        )
    return manifest


# Compatibility aliases make the API easy to consume from preflight/packaging
# code without exposing implementation details of the manifest format.
create_runtime_manifest = build_runtime_manifest
validate = validate_runtime_manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate a RoboStudio runtime integrity manifest")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    report = validate_runtime_manifest(args.root / "runtime" / MANIFEST_NAME)
    print(f"RoboStudio runtime integrity: PASS ({report['application_version']})")
