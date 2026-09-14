"""Compatibility contract for RoboStudio release artifacts."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Mapping
SCHEMA = "antechkids.robostudio.release-compatibility"
SCHEMA_VERSION = 1
_VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
class ReleaseCompatibilityError(RuntimeError):
    pass
@dataclass(frozen=True)
class Compatibility:
    application_version: str
    runtime_integrity_schema_version: int
    distribution_schema_version: int
    release_schema_version: int
    portable_python_required: bool
    bundled_platformio_required: bool

def parse_version(value: object, *, label: str = "version") -> tuple[int, int, int]:
    text = str(value).strip()
    match = _VERSION_RE.fullmatch(text)
    if not match:
        raise ReleaseCompatibilityError(f"Invalid {label}: expected MAJOR.MINOR.PATCH, got {text!r}")
    return tuple(int(part) for part in match.groups())

def build_compatibility(application_version: str, *, runtime_integrity_schema_version: int, distribution_schema_version: int, release_schema_version: int, portable_python_required: bool = False, bundled_platformio_required: bool = False) -> dict[str, object]:
    """Build compatibility metadata for legacy bundled-runtime or production host-prerequisite mode."""
    parse_version(application_version, label="application version")
    for name, value in (("runtime_integrity_schema_version", runtime_integrity_schema_version), ("distribution_schema_version", distribution_schema_version), ("release_schema_version", release_schema_version)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ReleaseCompatibilityError(f"Invalid {name}: {value!r}")
    if not isinstance(portable_python_required, bool) or not isinstance(bundled_platformio_required, bool):
        raise ReleaseCompatibilityError("Runtime prerequisite flags must be boolean")
    return {"schema": SCHEMA, "schema_version": SCHEMA_VERSION, "application_version": application_version.strip(), "runtime_integrity_schema_version": runtime_integrity_schema_version, "distribution_schema_version": distribution_schema_version, "release_schema_version": release_schema_version, "portable_python_required": portable_python_required, "bundled_platformio_required": bundled_platformio_required}

def read_compatibility(manifest: Mapping[str, object]) -> Compatibility:
    raw = manifest.get("compatibility")
    if not isinstance(raw, Mapping): raise ReleaseCompatibilityError("Release manifest has no compatibility contract")
    if raw.get("schema") != SCHEMA or raw.get("schema_version") != SCHEMA_VERSION: raise ReleaseCompatibilityError("Unsupported release compatibility schema")
    application_version = str(raw.get("application_version", "")).strip()
    parse_version(application_version, label="release application version")
    values = {}
    for name in ("runtime_integrity_schema_version", "distribution_schema_version", "release_schema_version"):
        value = raw.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1: raise ReleaseCompatibilityError(f"Invalid compatibility field: {name}")
        values[name] = value
    portable_python_required = raw.get("portable_python_required")
    bundled_platformio_required = raw.get("bundled_platformio_required")
    if not isinstance(portable_python_required, bool): raise ReleaseCompatibilityError("Invalid compatibility field: portable_python_required")
    if not isinstance(bundled_platformio_required, bool): raise ReleaseCompatibilityError("Invalid compatibility field: bundled_platformio_required")
    production = manifest.get("production_boundary") is True
    expected_prerequisite = not production
    mode = "production" if production else "legacy"
    if portable_python_required is not expected_prerequisite:
        expected_text = "True" if expected_prerequisite else "False"
        raise ReleaseCompatibilityError(f"Invalid compatibility field: portable Python must be {expected_text} for {mode} releases")
    if bundled_platformio_required is not expected_prerequisite:
        expected_text = "True" if expected_prerequisite else "False"
        raise ReleaseCompatibilityError(f"Invalid compatibility field: bundled PlatformIO must be {expected_text} for {mode} releases")
    return Compatibility(application_version=application_version, portable_python_required=portable_python_required, bundled_platformio_required=bundled_platformio_required, **values)

def validate_compatibility(manifest: Mapping[str, object], *, application_version: str | None = None, runtime_integrity_schema_version: int | None = None, distribution_schema_version: int | None = None, release_schema_version: int | None = None) -> Compatibility:
    contract = read_compatibility(manifest)
    if application_version is not None:
        expected = parse_version(application_version, label="runtime application version")
        actual = parse_version(contract.application_version, label="release application version")
        if actual[0] != expected[0]: raise ReleaseCompatibilityError(f"Incompatible application major version: release {contract.application_version}, runtime {application_version}")
        if actual > expected: raise ReleaseCompatibilityError(f"Release application version {contract.application_version} is newer than runtime {application_version}")
    for name, expected in (("runtime_integrity_schema_version", runtime_integrity_schema_version), ("distribution_schema_version", distribution_schema_version), ("release_schema_version", release_schema_version)):
        if expected is not None and getattr(contract, name) != expected: raise ReleaseCompatibilityError(f"Incompatible {name}: release {getattr(contract, name)}, runtime {expected}")
    return contract
build = build_compatibility
validate = validate_compatibility
