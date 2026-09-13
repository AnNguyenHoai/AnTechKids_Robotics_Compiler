"""RSD-21.1 production release boundary contract.

The production artifact contains the RoboStudio product and its application-
owned compiler/runtime assets. Host tools such as Python and PlatformIO are
not release payloads; they are target-machine prerequisites declared by the
release documentation and later qualification gates.

This module is deliberately declarative. It does not inspect or mutate a
release yet. RSD-21.3/RSD-21.4 will consume this contract when the assembly and
dependency-closure implementation is migrated to the new boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

SCHEMA = "antechkids.robostudio.release-boundary"
SCHEMA_VERSION = 1


class ReleaseOwnership(str, Enum):
    """Ownership determines whether an item belongs in the ZIP artifact."""

    APPLICATION = "application"
    TARGET_PREREQUISITE = "target-prerequisite"
    DEVELOPER_ONLY = "developer-only"


@dataclass(frozen=True)
class ReleaseBoundaryItem:
    """One named release boundary item and its packaging rule."""

    name: str
    ownership: ReleaseOwnership
    package: bool
    required_for: tuple[str, ...]
    rationale: str


# Canonical RSD-21.1 boundary. Keep this list small and explicit so a future
# assembly implementation cannot silently sweep a developer environment into
# the production ZIP.
BOUNDARY_ITEMS: tuple[ReleaseBoundaryItem, ...] = (
    ReleaseBoundaryItem(
        name="RoboStudio",
        ownership=ReleaseOwnership.APPLICATION,
        package=True,
        required_for=("ide", "compile", "hardware"),
        rationale="Primary end-user IDE/application delivered by the release.",
    ),
    ReleaseBoundaryItem(
        name="Compiler",
        ownership=ReleaseOwnership.APPLICATION,
        package=True,
        required_for=("compile", "hardware"),
        rationale="Application-owned compiler required to turn Robosim programs into robot output.",
    ),
    ReleaseBoundaryItem(
        name="Application resources",
        ownership=ReleaseOwnership.APPLICATION,
        package=True,
        required_for=("ide", "compile", "hardware"),
        rationale="Resources required by RoboStudio and the compiler at runtime.",
    ),
    ReleaseBoundaryItem(
        name="Application-local libraries and PE dependencies",
        ownership=ReleaseOwnership.APPLICATION,
        package=True,
        required_for=("ide", "compile", "hardware"),
        rationale="Non-system dependencies owned by the product must travel with the application.",
    ),
    ReleaseBoundaryItem(
        name="Release metadata",
        ownership=ReleaseOwnership.APPLICATION,
        package=True,
        required_for=("ide", "compile", "hardware"),
        rationale="Manifest, provenance, and integrity evidence identify and protect the artifact.",
    ),
    ReleaseBoundaryItem(
        name="Python",
        ownership=ReleaseOwnership.TARGET_PREREQUISITE,
        package=False,
        required_for=("compile",),
        rationale="Provided and maintained by the target machine according to the supported prerequisite contract.",
    ),
    ReleaseBoundaryItem(
        name="PlatformIO",
        ownership=ReleaseOwnership.TARGET_PREREQUISITE,
        package=False,
        required_for=("hardware",),
        rationale="Provided and maintained by the target machine according to the supported prerequisite contract.",
    ),
    ReleaseBoundaryItem(
        name="ESP32/USB driver",
        ownership=ReleaseOwnership.TARGET_PREREQUISITE,
        package=False,
        required_for=("hardware",),
        rationale="Installed on the target machine when hardware communication is required.",
    ),
    ReleaseBoundaryItem(
        name="Git",
        ownership=ReleaseOwnership.TARGET_PREREQUISITE,
        package=False,
        required_for=(),
        rationale="Not required by an installed production release.",
    ),
    ReleaseBoundaryItem(
        name="Source repository",
        ownership=ReleaseOwnership.DEVELOPER_ONLY,
        package=False,
        required_for=(),
        rationale="Production users consume the built artifact and must not need the source tree.",
    ),
    ReleaseBoundaryItem(
        name="Developer virtual environment",
        ownership=ReleaseOwnership.DEVELOPER_ONLY,
        package=False,
        required_for=(),
        rationale="Developer-only state must never become a production release dependency.",
    ),
)


def boundary_items() -> tuple[ReleaseBoundaryItem, ...]:
    """Return the immutable canonical boundary definition."""
    return BOUNDARY_ITEMS


def packaged_items() -> tuple[ReleaseBoundaryItem, ...]:
    """Return items that belong in the production artifact."""
    return tuple(item for item in BOUNDARY_ITEMS if item.package)


def target_prerequisites() -> tuple[ReleaseBoundaryItem, ...]:
    """Return prerequisites expected to be installed on the target machine."""
    return tuple(
        item for item in BOUNDARY_ITEMS if item.ownership is ReleaseOwnership.TARGET_PREREQUISITE
    )


def developer_only_items() -> tuple[ReleaseBoundaryItem, ...]:
    """Return inputs explicitly forbidden from becoming product dependencies."""
    return tuple(item for item in BOUNDARY_ITEMS if item.ownership is ReleaseOwnership.DEVELOPER_ONLY)


def to_dict() -> dict[str, object]:
    """Serialize the contract for release evidence and documentation tooling."""
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "artifact_model": "RoboStudio + Compiler",
        "items": [
            {
                "name": item.name,
                "ownership": item.ownership.value,
                "package": item.package,
                "required_for": list(item.required_for),
                "rationale": item.rationale,
            }
            for item in BOUNDARY_ITEMS
        ],
    }
