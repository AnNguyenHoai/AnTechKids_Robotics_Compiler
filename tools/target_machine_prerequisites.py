"""Canonical target-machine setup contract for RoboStudio releases.

The production artifact owns RoboStudio, Compiler and application resources.
Python, PlatformIO and board USB/UART drivers are provisioned externally on
the target machine. This module is declarative and side-effect free.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

SCHEMA = "antechkids.robostudio.target-machine-prerequisites"
SCHEMA_VERSION = 2
SUPPORTED_HOST_OS = "Windows 10/11 x64"
PATH_POLICY = "Required executable commands must be resolvable from the target user's PATH."


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
    install_command: str
    path_required: bool = True
    packaged: bool = False


# Python is required whenever the production application is used to compile
# or deploy robot programs. Hardware scope is cumulative with compile scope.
PREREQUISITES: tuple[TargetMachinePrerequisite, ...] = (
    TargetMachinePrerequisite(
        name="Python",
        kind=PrerequisiteKind.RUNTIME,
        required_for=(RequirementScope.COMPILE, RequirementScope.HARDWARE),
        command=("python", "--version"),
        version_policy=">=3.10, 64-bit",
        install_note="Install a supported 64-bit Python 3.10+ release and enable the Python command in PATH.",
        install_command="python -m pip --version",
    ),
    TargetMachinePrerequisite(
        name="PlatformIO Core",
        kind=PrerequisiteKind.TOOL,
        required_for=(RequirementScope.HARDWARE,),
        command=("pio", "--version"),
        version_policy="supported PlatformIO Core release",
        install_note="Install PlatformIO Core and ensure the pio command is available in PATH.",
        install_command="python -m pip install --upgrade platformio",
    ),
    TargetMachinePrerequisite(
        name="ESP32/USB driver",
        kind=PrerequisiteKind.DRIVER,
        required_for=(RequirementScope.HARDWARE,),
        command=(),
        version_policy="vendor-supported driver for the selected ESP32 USB/UART bridge",
        install_note="Install the USB/UART driver required by the connected ESP32 board before hardware deployment.",
        install_command="Install the driver supplied by the ESP32 board USB/UART bridge vendor.",
        path_required=False,
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
    """Validate invariants of the setup contract."""
    if not PREREQUISITES:
        raise ValueError("Target-machine prerequisite contract must not be empty")
    if not SUPPORTED_HOST_OS:
        raise ValueError("Supported host OS policy must be declared")
    if not PATH_POLICY:
        raise ValueError("PATH policy must be declared")
    names = [item.name for item in PREREQUISITES]
    if len(names) != len(set(names)):
        raise ValueError("Target prerequisite names must be unique")
    for item in PREREQUISITES:
        if item.packaged:
            raise ValueError(f"Target prerequisite must not be packaged: {item.name}")
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
        "host_model": "target-machine-prerequisites",
        "supported_host_os": SUPPORTED_HOST_OS,
        "path_policy": PATH_POLICY,
        "release_payload_policy": "Prerequisites are installed on the target machine; they are not bundled into the production ZIP.",
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
    }
