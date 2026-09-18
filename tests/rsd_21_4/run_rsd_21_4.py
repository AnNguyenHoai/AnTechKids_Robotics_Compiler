"""RSD-21.4 target-machine-aware qualification checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import target_machine_qualification, target_machine_prerequisites


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    target_machine_prerequisites.validate_contract()
    contract_payload = target_machine_prerequisites.to_dict()

    # Compile qualification must pass even with an empty host PATH: portable
    # Python and PlatformIO are release payload, not machine prerequisites.
    compile_report = target_machine_qualification.qualify_target_machine(
        scope=target_machine_prerequisites.RequirementScope.COMPILE,
        env={"PATH": ""},
    )
    compile_payload = target_machine_qualification.to_dict(compile_report)

    check("setup contract schema is stable", target_machine_prerequisites.SCHEMA == "antechkids.robostudio.target-machine-prerequisites")
    check("setup contract schema version is artifact-closed", target_machine_prerequisites.SCHEMA_VERSION == 4)
    check("supported host OS policy is declared", target_machine_prerequisites.SUPPORTED_HOST_OS == "Windows 10/11 x64")
    check("PATH policy rejects host runtime dependency", "must not require host Python" in target_machine_prerequisites.PATH_POLICY)
    check("setup contract is JSON serializable", bool(json.dumps(contract_payload)))
    check("portable Python is required bundled payload", "Portable Python runtime" in contract_payload["required_bundled_components"])
    check("PlatformIO is required bundled payload", "PlatformIO Core/runtime" in contract_payload["required_bundled_components"])
    check("driver does not require PATH", next(item for item in contract_payload["prerequisites"] if item["name"] == "ESP32/USB driver")["path_required"] is False)
    check("global Python host prerequisite is forbidden", "Global Python installation" in contract_payload["forbidden_host_prerequisites"])
    check("global PlatformIO host prerequisite is forbidden", "Global PlatformIO installation" in contract_payload["forbidden_host_prerequisites"])
    check("flash scope requires explicit serial readiness", "explicit serial port" in contract_payload["flash_readiness_policy"])

    check("qualification schema is stable", target_machine_qualification.SCHEMA == "antechkids.robostudio.target-machine-qualification")
    check("qualification schema version is artifact-closed", target_machine_qualification.SCHEMA_VERSION == 3)
    check("qualification references setup contract", compile_payload["setup_contract"]["schema"] == target_machine_prerequisites.SCHEMA)
    check("qualification records setup contract version", compile_payload["setup_contract"]["schema_version"] == target_machine_prerequisites.SCHEMA_VERSION)
    check("qualification records supported host OS", compile_payload["setup_contract"]["supported_host_os"] == target_machine_prerequisites.SUPPORTED_HOST_OS)
    check("qualification records required bundled runtime", "Portable Python runtime" in compile_payload["setup_contract"]["required_bundled_components"])
    check("compile scope is recorded", compile_report.scope == "compile")
    check("compile requires no external prerequisites", compile_report.prerequisites == ())
    check("compile qualification passes with empty host PATH", compile_report.passed)
    check("compile automated checks pass", compile_report.automated_checks_passed)
    check("compile qualification is JSON serializable", bool(json.dumps(compile_payload)))
    check("manual hardware check is not required for compile scope", compile_report.manual_checks_required is False)
    check("compile qualification has no flash evidence", compile_report.flash_preflight is None)

    # Host Python presence or absence must not influence compile qualification.
    python_host_report = target_machine_qualification.qualify_target_machine(
        scope="compile",
        env={"PATH": str(Path(sys.executable).parent)},
    )
    check("host Python does not change compile prerequisite set", python_host_report.prerequisites == ())
    check("host Python does not change compile qualification", python_host_report.passed is True)

    hardware_report = target_machine_qualification.qualify_target_machine(
        scope="hardware",
        env={"PATH": ""},
    )
    hardware_items = target_machine_prerequisites.for_scope("hardware")
    hardware_names = {item.name for item in hardware_items}
    check("hardware scope excludes host Python", "Python" not in hardware_names)
    check("hardware scope excludes host PlatformIO", "PlatformIO Core" not in hardware_names)
    check("hardware scope includes driver", "ESP32/USB driver" in hardware_names)
    check("hardware driver is explicitly manual", next(i for i in hardware_items if i.name == "ESP32/USB driver").kind is target_machine_prerequisites.PrerequisiteKind.DRIVER)
    check("hardware automated qualification passes without host tools", hardware_report.passed is True)
    check("hardware qualification records manual driver check", hardware_report.manual_checks_required is True)
    check("hardware prerequisite result is manual", hardware_report.prerequisites[0].validation == "manual")
    check("hardware policy scope does not pretend a port is visible", hardware_report.flash_preflight is None)

    print("RSD-21.4 target-machine-aware qualification checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
