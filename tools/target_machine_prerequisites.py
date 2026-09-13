"""RSD-21.2 target-machine prerequisite contract.

The production ZIP contains RoboStudio and the application-owned compiler.
Host tooling is provisioned on the target machine and is intentionally not
copied from the developer/build machine into the release artifact.

This module is declarative and side-effect free. Later release qualification
and installer tooling can consume this contract without duplicating the
prerequisite policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

SCHEMA = "antechkids.robostudio.target-machine-prerequisites"
SCHEMA_VERSION = 1


class PrerequisiteKind(str, Enum):
    """Classification used by the target-machine prerequisite contract."""

    RUNTIME = "runtime"
    TOOL = "tool"
    DRIVER = "driver"


class RequirementScope(str, Enum):
    """When a prerequisite is needed on the target machine."""

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
    packaged: bool = False


# Keep versions conservative until the project toolchain pins exact versions.
# The contract records the minimum supported runtime/tool major line rather
# than silently inheriting whatever happens to be installed on the developer
# machine. Exact versions can be tightened here as the production toolchain is
# formally pinned.
PREREQUISITES: tuple[TargetMachinePrerequisite, ...] = (
    TargetMachinePrerequisite(
        name="Python",
        kind=PrerequisiteKind.RUNTIME,
        required_for=(RequirementScope.COMPILE,),
        command=("python", "--version"),
        version_policy=">=3.10",
        install_note="Install a supported 64-bit Python 3.10+ release and ensure the python command is available to the target user.",
    ),
    TargetMachinePrerequisite(
        name="PlatformIO Core",
        kind=PrerequisiteKind.TOOL,
        required_for=(RequirementScope.HARDWARE,),
        command=("pio", "--version"),
        version_policy="supported PlatformIO Core release",
        install_note="Install PlatformIO Core and ensure the pio command is available to the target user.",
    ),
    TargetMachinePrerequisite(
        name="ESP32/USB driver",
        kind=PrerequisiteKind.DRIVER,
        required_for=(RequirementScope.HARDWARE,),
        command=(),
        version_policy="vendor-supported driver for the selected ESP32 USB/UART bridge",
        install_note="Install the USB/UART driver required by the connected ESP32 board before hardware deployment.",
    ),
)


FORBIDDEN_BUNDLED_PREREQUISITES: tuple[str, ...] = (
    "Python installation",
    "PlatformIO installation",
    "Developer virtual environment",
    "Developer source repository",
)


def prerequisites() -> tuple[TargetMachinePrerequisite, ...]:
    """Return the canonical target-machine prerequisite list."""
    return PREREQUISITES


def for_scope(scope: RequirementScope | str) -> tuple[TargetMachinePrerequisite, ...]:
    """Return prerequisites required for a compile or hardware scope."""
    scope = RequirementScope(scope)
    return tuple(item for item in PREREQUISITES if scope in item.required_for)


def validate_contract() -> None:
    """Validate invariants of the prerequisite contract."""
    if not PREREQUISITES:
        raise ValueError("Target-machine prerequisite contract must not be empty")
    names = [item.name for item in PREREQUISITES]
    if len(names) != len(set(names)):
        raise ValueError("Target-machine prerequisite names must be unique")
    for item in PREREQUISITES:
        if item.packaged:
            raise ValueError(f"Target prerequisite must not be packaged: {item.name}")
        if not item.required_for:
            raise ValueError(f"Target prerequisite must declare a scope: {item.name}")
        if item.kind is not PrerequisiteKind.DRIVER and not item.command:
            raise ValueError(f"Executable prerequisite must declare a validation command: {item.name}")


def to_dict() -> dict[str, object]:
    """Serialize the contract for release evidence and user documentation."""
    validate_contract()
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "host_model": "target-machine-prerequisites",
        "release_payload_policy": "Prerequisites are installed on the target machine; they are not bundled into the production ZIP.",
        "prerequisites": [
            {
                "name": item.name,
                "kind": item.kind.value,
                "required_for": [scope.value for scope in item.required_for],
                "validation_command": list(item.command),
                "version_policy": item.version_policy,
                "packaged": item.packaged,
                "install_note": item.install_note,
            }
            for item in PREREQUISITES
        ],
        "forbidden_bundled_prerequisites": list(FORBIDDEN_BUNDLED_PREREQUISITES),
    }
