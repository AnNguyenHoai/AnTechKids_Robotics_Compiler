"""Canonical target-machine setup contract for portable RoboStudio releases.

B2.2 defines a copy-and-run production model: Python and PlatformIO belong to
the release artifact and must never be prerequisites installed on the target
machine. The only external hardware prerequisite is the board-specific USB/UART
driver when Windows does not already provide it.

This module is declarative and side-effect free.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

SCHEMA = "antechkids.robostudio.target-machine-prerequisites"
SCHEMA_VERSION = 3
SUPPORTED_HOST_OS = "Windows 10/11 x64"
PATH_POLICY = (
    "RoboStudio compile/deploy must not require host Python or PlatformIO on PATH; "
    "production subprocesses resolve application-owned tools from the extracted artifact."
)


class PrerequisiteKind(str, Enum):
    """Classification used by the target-machine prerequisite contract."""

    RUNTIME = "runtime"
    TOOL = "tool"
    DRIVER = "driver"


class RequirementScope(str, Enum):
    """When an external prerequisite is needed on the target machine."""

    COMPILE = "compile"
    HARDWARE = "hardware"


@dataclass(frozen=True)
class TargetMachinePrerequisite:
    """One externally provisioned prerequisite required by the release."""

    name: str
    kind: PrerequisiteKind
    required_for: tuple[RequirementScope, ...]
    command: tuple[str, ...]
    version_policy: str
    install_note: str
    install_command: str
    path_required: bool = True
    packaged: bool = False


# Python and PlatformIO are intentionally absent: they are mandatory release
# payload, not host setup. Hardware deployment may still require a vendor USB
# driver depending on the ESP32 USB/UART bridge and Windows driver inventory.
PREREQUISITES: tuple[TargetMachinePrerequisite, ...] = (
    TargetMachinePrerequisite(
        name="ESP32/USB driver",
        kind=PrerequisiteKind.DRIVER,
        required_for=(RequirementScope.HARDWARE,),
        command=(),
        version_policy="vendor-supported driver for the selected ESP32 USB/UART bridge",
        install_note=(
            "Install the USB/UART driver required by the connected ESP32 board only "
            "when Windows does not already provide a compatible driver."
        ),
        install_command="Install the driver supplied by the ESP32 board USB/UART bridge vendor.",
        path_required=False,
    ),
)

REQUIRED_BUNDLED_COMPONENTS: tuple[str, ...] = (
    "Portable Python runtime",
    "PlatformIO Core/runtime",
)

# These remain forbidden inside the production ZIP. They are development state,
# not runtime dependencies.
FORBIDDEN_BUNDLED_PREREQUISITES: tuple[str, ...] = (
    "Developer virtual environment",
    "Developer source repository",
)

# A clean target machine must not need these global installations for normal
# RoboStudio compile/deploy flows.
FORBIDDEN_HOST_PREREQUISITES: tuple[str, ...] = (
    "Global Python installation",
    "Global PlatformIO installation",
    "Developer virtual environment",
    "Developer source repository",
)


def prerequisites() -> tuple[TargetMachinePrerequisite, ...]:
    """Return the canonical external target-machine prerequisite list."""
    return PREREQUISITES


def for_scope(scope: RequirementScope | str) -> tuple[TargetMachinePrerequisite, ...]:
    """Return external prerequisites required for a compile or hardware scope."""
    scope = RequirementScope(scope)
    return tuple(item for item in PREREQUISITES if scope in item.required_for)


def validate_contract() -> None:
    """Validate invariants of the copy-and-run target-machine contract."""
    if not SUPPORTED_HOST_OS:
        raise ValueError("Supported host OS policy must be declared")
    if not PATH_POLICY:
        raise ValueError("PATH policy must be declared")
    if not REQUIRED_BUNDLED_COMPONENTS:
        raise ValueError("Portable release must declare bundled runtime components")
    names = [item.name for item in PREREQUISITES]
    if len(names) != len(set(names)):
        raise ValueError("Target prerequisite names must be unique")
    if any(name in {"Python", "PlatformIO Core"} for name in names):
        raise ValueError("Python and PlatformIO must be bundled, not target-machine prerequisites")
    for item in PREREQUISITES:
        if item.packaged:
            raise ValueError(f"External target prerequisite must not be packaged: {item.name}")
        if not item.required_for:
            raise ValueError(f"Target prerequisite must declare a scope: {item.name}")
        if item.kind is not PrerequisiteKind.DRIVER and not item.command:
            raise ValueError(f"Executable prerequisite must declare a validation command: {item.name}")
        if not item.version_policy or not item.install_note or not item.install_command:
            raise ValueError(f"Target prerequisite must declare setup policy: {item.name}")
        if item.kind is PrerequisiteKind.DRIVER and item.path_required:
            raise ValueError(f"Driver prerequisite must not require PATH resolution: {item.name}")


def to_dict() -> dict[str, object]:
    """Serialize the canonical setup contract for documentation and tooling."""
    validate_contract()
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "host_model": "artifact-closed-copy-and-run",
        "supported_host_os": SUPPORTED_HOST_OS,
        "path_policy": PATH_POLICY,
        "release_payload_policy": (
            "Portable Python and PlatformIO are bundled in the production ZIP. "
            "The target machine must not install them for RoboStudio compile/deploy."
        ),
        "required_bundled_components": list(REQUIRED_BUNDLED_COMPONENTS),
        "prerequisites": [
            {
                "name": item.name,
                "kind": item.kind.value,
                "required_for": [scope.value for scope in item.required_for],
                "validation_command": list(item.command),
                "version_policy": item.version_policy,
                "install_command": item.install_command,
                "install_note": item.install_note,
                "path_required": item.path_required,
                "packaged": item.packaged,
            }
            for item in PREREQUISITES
        ],
        "forbidden_bundled_prerequisites": list(FORBIDDEN_BUNDLED_PREREQUISITES),
        "forbidden_host_prerequisites": list(FORBIDDEN_HOST_PREREQUISITES),
    }
