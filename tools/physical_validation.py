"""H26-N physical validation preflight.

This module verifies the deployment evidence that can be checked without
assuming that a robot is physically connected. It never claims that motors,
sensors, or the serial transport were physically exercised.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.deployment_contract import DeploymentContractError, validate_manifest

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 1
REPORT_KIND = "robot_physical_validation_report"


class PhysicalValidationError(RuntimeError):
    """Raised when deployment evidence fails a physical-validation preflight."""


def _check_generated_program(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PhysicalValidationError(f"Generated firmware artifact is missing: {path}")
    text = path.read_text(encoding="utf-8")
    required = ("const Instruction generatedProgram[]", "generatedProgramSize")
    missing = [token for token in required if token not in text]
    if missing:
        raise PhysicalValidationError(f"Generated firmware artifact is incomplete: {missing}")
    return {"path": str(path), "instruction_table_present": True, "size": path.stat().st_size}


def validate_deployment(manifest_path: Path, *, expected_target: str = "esp32") -> dict[str, Any]:
    """Validate deployable artifacts and return an evidence report.

    The report explicitly separates host-verifiable checks from physical checks.
    A connected device is therefore never implied by a successful preflight.
    """
    try:
        manifest = validate_manifest(Path(manifest_path), expected_target=expected_target)
    except DeploymentContractError as exc:
        raise PhysicalValidationError(str(exc)) from exc

    generated = ROOT / "robot-platform" / "main" / "src" / "Application" / "generated_program.h"
    generated_evidence = _check_generated_program(generated)

    program = manifest["artifacts"]["program_header"]
    generated_bytes = generated.read_bytes()
    source_bytes = Path(program["path"]).read_bytes()
    artifact_matches_firmware_input = generated_bytes == source_bytes

    if not artifact_matches_firmware_input:
        raise PhysicalValidationError(
            "Firmware generated_program.h does not match the manifest program_header artifact"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": REPORT_KIND,
        "target": manifest["target"],
        "platformio_environment": manifest.get("platformio_environment"),
        "required_capabilities": manifest["required_capabilities"],
        "checks": {
            "deployment_manifest_valid": True,
            "generated_program_present": True,
            "generated_program_matches_manifest_artifact": True,
            "physical_device_connected": False,
            "physical_motion_verified": False,
            "physical_sensors_verified": False,
        },
        "generated_program": generated_evidence,
        "physical_validation_required": True,
    }


def write_report(report: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
