"""RSD-21.3 production artifact boundary enforcement.

The production release payload is the RoboStudio application and its
application-owned compiler/resources/dependencies. Target-machine tools such
as Python and PlatformIO are prerequisites, not payload. This module provides
the executable enforcement point used by production distribution assembly and
release validation.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools import release_boundary

SCHEMA = "antechkids.robostudio.production-artifact-boundary"
SCHEMA_VERSION = 1
BOUNDARY_MANIFEST = "release-boundary.json"

# These paths are intentionally structural rather than installation-specific.
# A production artifact may contain application resources below runtime/, but
# it must never contain a bundled host-tool installation at these roots.
FORBIDDEN_PAYLOAD_ROOTS: tuple[Path, ...] = (
    Path("runtime/bin"),
    Path("runtime/platformio"),
)

FORBIDDEN_PAYLOAD_NAMES: frozenset[str] = frozenset({
    ".venv",
    ".pio",
    "penv",
})


class ProductionArtifactBoundaryError(RuntimeError):
    """Raised when a production distribution crosses the release boundary."""


def _normal(path: Path) -> str:
    return path.as_posix().strip("/").lower()


def _is_forbidden(relative: Path) -> bool:
    normalized = _normal(relative)
    parts = normalized.split("/") if normalized else []
    if any(part in FORBIDDEN_PAYLOAD_NAMES for part in parts):
        return True
    return any(
        normalized == _normal(root) or normalized.startswith(_normal(root) + "/")
        for root in FORBIDDEN_PAYLOAD_ROOTS
    )


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
            "Production artifact contains target/developer prerequisite payload: "
            + ", ".join(violations)
        )

    # The RSD-21.1 contract is the policy source of truth. Keep an explicit
    # assertion here so a future boundary change cannot silently invalidate the
    # enforcement layer.
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
        "artifact_model": "RoboStudio + Compiler",
        "boundary_schema": release_boundary.SCHEMA,
        "boundary_schema_version": release_boundary.SCHEMA_VERSION,
        "status": "PASS",
        "forbidden_payload_roots": [item.as_posix() for item in FORBIDDEN_PAYLOAD_ROOTS],
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
