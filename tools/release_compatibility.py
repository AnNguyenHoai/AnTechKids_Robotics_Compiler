"""Compatibility contract for portable RoboStudio release artifacts.

RSD-15 defines the metadata that lets a release identify the application/runtime
contract it was built for. Compatibility is deliberately strict for schema
versions and portable-runtime requirements: a release must not be accepted when
its manifest is ambiguous, malformed, or built against a different contract.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

SCHEMA = "antechkids.robostudio.release-compatibility"
SCHEMA_VERSION = 1

_VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ReleaseCompatibilityError(RuntimeError):
    """Raised when a release cannot be proven compatible with the runtime."""


@dataclass(frozen=True)
class Compatibility:
    """Normalized compatibility contract carried by a release manifest."""

    application_version: str
    runtime_integrity_schema_version: int
    distribution_schema_version: int
    release_schema_version: int
    portable_python_required: bool
    bundled_platformio_required: bool


def parse_version(value: object, *, label: str = "version") -> tuple[int, int, int]:
    """Parse the supported MAJOR.MINOR.PATCH application version format."""
    text = str(value).strip()
    match = _VERSION_RE.fullmatch(text)
    if not match:
        raise ReleaseCompatibilityError(
            f"Invalid {label}: expected MAJOR.MINOR.PATCH, got {text!r}"
        )
    return tuple(int(part) for part in match.groups())


def build_compatibility(
    application_version: str,
    *,
    runtime_integrity_schema_version: int,
    distribution_schema_version: int,
    release_schema_version: int,
    portable_python_required: bool = True,
    bundled_platformio_required: bool = True,
) -> dict[str, object]:
    """Build the authoritative compatibility descriptor for a release."""
    parse_version(application_version, label="application version")
    for name, value in (
        ("runtime_integrity_schema_version", runtime_integrity_schema_version),
        ("distribution_schema_version", distribution_schema_version),
        ("release_schema_version", release_schema_version),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ReleaseCompatibilityError(f"Invalid {name}: {value!r}")
    if not portable_python_required or not bundled_platformio_required:
        raise ReleaseCompatibilityError(
            "Portable releases require application-owned Python and PlatformIO"
        )
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "application_version": application_version.strip(),
        "runtime_integrity_schema_version": runtime_integrity_schema_version,
        "distribution_schema_version": distribution_schema_version,
        "release_schema_version": release_schema_version,
        "portable_python_required": True,
        "bundled_platformio_required": True,
    }


def read_compatibility(manifest: Mapping[str, object]) -> Compatibility:
    """Validate and normalize a compatibility descriptor from a manifest."""
    raw = manifest.get("compatibility")
    if not isinstance(raw, Mapping):
        raise ReleaseCompatibilityError("Release manifest has no compatibility contract")
    if raw.get("schema") != SCHEMA or raw.get("schema_version") != SCHEMA_VERSION:
        raise ReleaseCompatibilityError("Unsupported release compatibility schema")

    application_version = str(raw.get("application_version", "")).strip()
    parse_version(application_version, label="release application version")

    values = {}
    for name in (
        "runtime_integrity_schema_version",
        "distribution_schema_version",
        "release_schema_version",
    ):
        value = raw.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ReleaseCompatibilityError(f"Invalid compatibility field: {name}")
        values[name] = value

    if raw.get("portable_python_required") is not True:
        raise ReleaseCompatibilityError("Release compatibility requires portable Python")
    if raw.get("bundled_platformio_required") is not True:
        raise ReleaseCompatibilityError("Release compatibility requires bundled PlatformIO")

    return Compatibility(
        application_version=application_version,
        portable_python_required=True,
        bundled_platformio_required=True,
        **values,
    )


def validate_compatibility(
    manifest: Mapping[str, object],
    *,
    application_version: str | None = None,
    runtime_integrity_schema_version: int | None = None,
    distribution_schema_version: int | None = None,
    release_schema_version: int | None = None,
) -> Compatibility:
    """Validate a release contract against the runtime/application contract.

    Application versions use the conservative same-major compatibility rule;
    schema versions are exact because a schema change can alter semantics.
    """
    contract = read_compatibility(manifest)
    if application_version is not None:
        expected = parse_version(application_version, label="runtime application version")
        actual = parse_version(contract.application_version, label="release application version")
        if actual[0] != expected[0]:
            raise ReleaseCompatibilityError(
                f"Incompatible application major version: release {contract.application_version}, "
                f"runtime {application_version}"
            )
        if actual > expected:
            raise ReleaseCompatibilityError(
                f"Release application version {contract.application_version} is newer than runtime {application_version}"
            )

    for name, expected in (
        ("runtime_integrity_schema_version", runtime_integrity_schema_version),
        ("distribution_schema_version", distribution_schema_version),
        ("release_schema_version", release_schema_version),
    ):
        if expected is not None and getattr(contract, name) != expected:
            raise ReleaseCompatibilityError(
                f"Incompatible {name}: release {getattr(contract, name)}, runtime {expected}"
            )
    return contract


build = build_compatibility
validate = validate_compatibility
