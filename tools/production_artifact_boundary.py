"""RSD-21.3 production artifact boundary enforcement.

The production release payload includes application-owned runtime assets. RSD-23
moved Python and PlatformIO from target prerequisites into the application-owned
release boundary so a clean Windows machine can run the product without a
pre-installed developer environment. Developer-only payloads remain forbidden.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools import release_boundary

SCHEMA = "antechkids.robostudio.production-artifact-boundary"
SCHEMA_VERSION = 1
BOUNDARY_MANIFEST = "release-boundary.json"

# These names are always development state and must never be copied into the
# production artifact. Runtime/bin and runtime/platformio are now valid because
# they are application-owned release payload roots under RSD-23.
FORBIDDEN_PAYLOAD_NAMES: frozenset[str] = frozenset({
    ".git",
    ".venv",
    ".pio",
    "penv",
    "__pycache__",
    ".pytest_cache",
})


class ProductionArtifactBoundaryError(RuntimeError):
    """Raised when a production distribution crosses the release boundary."""


def _normal(path: Path) -> str:
    return path.as_posix().strip("/").lower()


def _is_forbidden(relative: Path) -> bool:
    normalized = _normal(relative)
    parts = normalized.split("/") if normalized else []
    return any(part in FORBIDDEN_PAYLOAD_NAMES for part in parts)


def validate_distribution_root(root: Path) -> dict[str, object]:
    """Validate that ``root`` contains only allowed production payload paths.

    The check is deliberately filesystem based and therefore catches both
    files and directories that a later ZIP step would otherwise package.
    """
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ProductionArtifactBoundaryError(f"Production distribution not found: {root}")

    violations: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().lower()):
        relative = path.relative_to(root)
        if _is_forbidden(relative):
            violations.append(relative.as_posix())

    if violations:
        raise ProductionArtifactBoundaryError(
            "Production artifact contains developer-only payload: " + ", ".join(violations)
        )

    for item in release_boundary.packaged_items():
        if item.package is not True or item.ownership is not release_boundary.ReleaseOwnership.APPLICATION:
            raise ProductionArtifactBoundaryError(
                f"Invalid packaged release-boundary item: {item.name}"
            )
    for item in release_boundary.target_prerequisites():
        if item.package:
            raise ProductionArtifactBoundaryError(
                f"Target prerequisite is marked for packaging: {item.name}"
            )

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "artifact_model": "RoboStudio + Compiler + Application-Owned Runtime",
        "boundary_schema": release_boundary.SCHEMA,
        "boundary_schema_version": release_boundary.SCHEMA_VERSION,
        "status": "PASS",
        "forbidden_payload_names": sorted(FORBIDDEN_PAYLOAD_NAMES),
    }


def write_boundary_manifest(root: Path, output: Path | None = None) -> Path:
    """Write machine-readable boundary evidence for an assembled distribution."""
    root = Path(root).expanduser().resolve()
    validate_distribution_root(root)
    path = Path(output) if output is not None else root / BOUNDARY_MANIFEST
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(validate_distribution_root(root), indent=2) + "\n",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate the RoboStudio production artifact boundary")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    report = validate_distribution_root(args.root)
    print(f"RSD-21.3 production artifact boundary: {report['status']}")
