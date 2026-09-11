"""Deterministic application-owned runtime resource resolution.

RoboStudio distribution resources must be relocatable and independent of the
current working directory. Frozen applications consume resources only from
``runtime/resources``. Source development keeps a repository fallback so the
existing developer workflow remains usable.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

from tools.runtime_paths import (
    APPLICATION_HOME_ENV,
    application_root,
    is_frozen,
    runtime_root,
)

RESOURCE_ROOT_NAME = Path("runtime") / "resources"
RESOURCE_MANIFEST_NAME = "runtime-resources.json"
RESOURCE_SPECS = {
    "target_profiles": Path("robot-isa") / "target_profiles.json",
}

SOURCE_RESOURCE_ROOT = Path(__file__).resolve().parents[1] / "packages"


class RuntimeResourceError(RuntimeError):
    """Raised when an application-owned runtime resource is invalid or missing."""


def runtime_resource_root() -> Path:
    """Return the application-owned runtime resource root.

    Use the same explicit ``ROBOSTUDIO_HOME`` path identity as the runtime
    directory rather than rebuilding it through ``application_root()``.  The
    latter canonicalizes the environment override, which can change the
    lexical path identity used by packaged/test layouts on Windows.
    """
    return runtime_root() / "resources"


def _source_resource_root() -> Path:
    return SOURCE_RESOURCE_ROOT


def _validate_name(name: str) -> Path:
    relative = RESOURCE_SPECS.get(name)
    if relative is None:
        raise RuntimeResourceError(f"Unknown RoboStudio runtime resource: {name}")
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeResourceError(f"Invalid runtime resource specification: {name}")
    return relative


def resolve_resource(name: str, *, required: bool = True) -> Path | None:
    """Resolve a named runtime resource without consulting CWD or PATH."""
    relative = _validate_name(name)
    if is_frozen() or os.environ.get(APPLICATION_HOME_ENV):
        candidate = runtime_resource_root() / relative
    else:
        candidate = _source_resource_root() / relative
    if candidate.is_file():
        return candidate
    if required:
        mode = "packaged" if is_frozen() else "source"
        raise RuntimeResourceError(
            f"Required {mode} RoboStudio runtime resource is missing: {candidate}"
        )
    return None


def resource_manifest_path() -> Path:
    return runtime_resource_root() / RESOURCE_MANIFEST_NAME


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_resource_manifest(root: Path | None = None, resources: Iterable[str] | None = None) -> dict:
    root = Path(root) if root is not None else runtime_resource_root()
    names = tuple(resources) if resources is not None else tuple(RESOURCE_SPECS)
    entries: dict[str, dict] = {}
    for name in names:
        relative = _validate_name(name)
        path = root / relative
        if not path.is_file():
            raise RuntimeResourceError(f"Runtime resource is missing: {path}")
        entries[name] = {
            "path": relative.as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return {"schema": "antechkids.robostudio.runtime-resources", "schema_version": 1, "resources": entries}


def write_resource_manifest(root: Path | None = None, resources: Iterable[str] | None = None) -> Path:
    root = Path(root) if root is not None else runtime_resource_root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / RESOURCE_MANIFEST_NAME
    path.write_text(json.dumps(build_resource_manifest(root, resources), indent=2) + "\n", encoding="utf-8")
    return path


def validate_resource_manifest(path: Path | None = None) -> dict:
    manifest_path = Path(path) if path is not None else resource_manifest_path()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeResourceError(f"Unable to load runtime resource manifest: {exc}") from exc
    if manifest.get("schema") != "antechkids.robostudio.runtime-resources" or manifest.get("schema_version") != 1:
        raise RuntimeResourceError("Unsupported runtime resource manifest schema")
    root = manifest_path.parent
    for name, entry in manifest.get("resources", {}).items():
        relative = _validate_name(name)
        if entry.get("path") != relative.as_posix():
            raise RuntimeResourceError(f"Runtime resource manifest path mismatch: {name}")
        resource = root / relative
        try:
            resource.relative_to(root)
        except ValueError as exc:
            raise RuntimeResourceError(f"Runtime resource escapes application resource root: {name}") from exc
        if not resource.is_file():
            raise RuntimeResourceError(f"Runtime resource is missing: {resource}")
        if resource.stat().st_size != entry.get("size"):
            raise RuntimeResourceError(f"Runtime resource size changed: {name}")
        if sha256_file(resource) != entry.get("sha256"):
            raise RuntimeResourceError(f"Runtime resource checksum mismatch: {name}")
    return manifest
