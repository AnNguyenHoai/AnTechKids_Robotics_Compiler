"""Runtime projection of the H35 compatibility policy.

The authoritative compatibility matrix lives in
``packages/robot-isa/compatibility_policy.json``. This module is deliberately
small so frozen RoboStudio builds can enforce the same policy without reading
repository files at runtime. The H35 CI gate verifies this projection against
the authoritative policy and fails on drift.
"""
from __future__ import annotations

CURRENT_RELEASE = "0.1.1"
CURRENT_COMPILER_GENERATION = 1
CURRENT_FIRMWARE_GENERATION = 1
LEGACY_UNVERSIONED_FIRMWARE_GENERATION = 0
KNOWN_FIRMWARE_GENERATIONS = frozenset({0, 1})
SUPPORTED_OTA_SOURCE_GENERATIONS = frozenset({0, 1})


def normalize_firmware_generation(value: object | None) -> int:
    """Return a validated, explicitly known firmware generation.

    Firmware shipped before H35 did not advertise a generation. Missing data
    is therefore the one explicitly defined legacy generation (0), not an
    arbitrary wildcard. Any explicit unknown/future generation fails closed so
    compatibility is never inferred from numeric ordering or semantic version.
    """
    if value is None:
        return LEGACY_UNVERSIONED_FIRMWARE_GENERATION
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("invalid robot compatibility generation")
    if value not in KNOWN_FIRMWARE_GENERATIONS:
        raise ValueError(f"unsupported robot compatibility generation: {value}")
    return value


def ota_compatibility_error(firmware_generation: int) -> str | None:
    """Return an actionable error when this RoboStudio must not OTA the robot."""
    if firmware_generation in SUPPORTED_OTA_SOURCE_GENERATIONS:
        return None
    return (
        "Robot firmware compatibility generation "
        f"{firmware_generation} is not supported by RoboStudio compiler generation "
        f"{CURRENT_COMPILER_GENERATION}. Update RoboStudio or use an explicitly "
        "supported migration path; compatibility is never inferred automatically."
    )


def flashed_firmware_compatibility_error(firmware_generation: int) -> str | None:
    """Verify that a firmware image just flashed by this release is current."""
    if firmware_generation == CURRENT_FIRMWARE_GENERATION:
        return None
    return (
        "Firmware verification reported compatibility generation "
        f"{firmware_generation}; this RoboStudio release must produce generation "
        f"{CURRENT_FIRMWARE_GENERATION}. The deployment is not considered verified."
    )
