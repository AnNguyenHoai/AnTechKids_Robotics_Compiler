"""RSD-P0 production runtime dependency closure enforcement.

The production ZIP must be self-consistent: every application-owned runtime
entry required by the production contract is present, every packaged payload
file is represented by the distribution inventory, and developer/host
execution state never crosses the release boundary.

This gate intentionally does not package Python, PlatformIO, USB drivers, or
other target prerequisites. Those remain external prerequisites under the
production release-boundary contract.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools import distribution_package, production_artifact_boundary, runtime_resources

SCHEMA = "antechkids.robostudio.production-runtime-closure"
SCHEMA_VERSION = 1

FORBIDDEN_NAMES = frozenset({
    ".git",
    ".venv",
    ".pio",
    "penv",
    "__pycache__",
    ".pytest_cache",
})


def _required_paths(root: Path, application: str) -> tuple[Path, ...]:
    """Return the canonical application-owned runtime closure."""
    return (
        Path(application),
        Path("VERSION"),
        Path("compiler") / "main.py",
        Path("compiler") / "robostudio_bridge.py",
        Path("compiler") / "compiler",
        Path("compiler") / "frontend" / "__init__.py",
        Path("compiler") / "frontend" / "rewriter.py",
        Path("runtime") / "resources" / runtime_resources.RESOURCE_MANIFEST_NAME,
        Path("runtime") / "resources" / "robot-isa" / "target_profiles.json",
    )


def _payload_files(root: Path) -> set[str]:
    excluded = {
        distribution_package.DISTRIBUTION_MANIFEST,
        production_artifact_boundary.BOUNDARY_MANIFEST,
    }
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name not in excluded
    }


def _manifest_files(root: Path, manifest: dict) -> set[str]:
    result: set[str] = set()
    for entry in manifest.get("files", []):
        relative = Path(str(entry.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"Distribution manifest path escapes root: {relative}")
        result.add(relative.as_posix())
    return result


def _validate_forbidden_payload(root: Path) -> list[str]:
    violations: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part.lower() in FORBIDDEN_NAMES for part in relative.parts):
            violations.append(relative.as_posix())
    return sorted(violations, key=str.lower)


def validate_distribution(root: Path) -> dict[str, object]:
    """Validate the complete production runtime dependency closure."""
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"Production distribution not found: {root}")

    manifest_path = root / distribution_package.DISTRIBUTION_MANIFEST
    manifest = distribution_package.validate_distribution_manifest(manifest_path)
    if manifest.get("production_boundary") is not True:
        raise RuntimeError("Production runtime closure requires production_boundary=true")

    application = str(manifest.get("application", "")).strip()
    if not application or Path(application).name != application or Path(application).suffix.lower() != ".exe":
        raise RuntimeError("Production distribution manifest must identify a single executable")

    required = _required_paths(root, application)
    missing = [path.as_posix() for path in required if not (root / path).exists()]
    if missing:
        raise RuntimeError("Production runtime closure is missing: " + ", ".join(missing))

    manifest_files = _manifest_files(root, manifest)
    payload_files = _payload_files(root)
    untracked = sorted(payload_files - manifest_files, key=str.lower)
    if untracked:
        raise RuntimeError("Production payload is not covered by distribution manifest: " + ", ".join(untracked))

    missing_inventory = sorted(manifest_files - payload_files, key=str.lower)
    if missing_inventory:
        raise RuntimeError("Distribution manifest references missing payload files: " + ", ".join(missing_inventory))

    forbidden = _validate_forbidden_payload(root)
    if forbidden:
        raise RuntimeError("Production runtime closure contains developer-only payload: " + ", ".join(forbidden))

    resource_manifest = runtime_resources.validate_resource_manifest(
        root / "runtime" / "resources" / runtime_resources.RESOURCE_MANIFEST_NAME
    )

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "application": application,
        "required_paths": [path.as_posix() for path in required],
        "payload_file_count": len(payload_files),
        "runtime_resource_manifest": resource_manifest["schema"],
        "production_boundary": True,
    }


def write_evidence(root: Path, output: Path | None = None) -> Path:
    """Write machine-readable dependency-closure evidence."""
    root = Path(root).expanduser().resolve()
    evidence = validate_distribution(root)
    path = Path(output) if output is not None else root / "production-runtime-closure.json"
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return path
