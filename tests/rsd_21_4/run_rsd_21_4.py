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

    compile_report = target_machine_qualification.qualify_target_machine(
        scope=target_machine_prerequisites.RequirementScope.COMPILE,
        env={"PATH": str(Path(sys.executable).parent)},
    )
    compile_payload = target_machine_qualification.to_dict(compile_report)
    python_result = next(item for item in compile_report.prerequisites if item.name == "Python")

    check("qualification schema is stable", target_machine_qualification.SCHEMA == "antechkids.robostudio.target-machine-qualification")
    check("qualification schema version is stable", target_machine_qualification.SCHEMA_VERSION == 1)
    check("compile scope is recorded", compile_report.scope == "compile")
    check("Python is checked for compile scope", python_result.required)
    check("Python is available for test environment", python_result.available)
    check("Python validation is command based", python_result.validation == "command-pass")
    check("compile qualification passes", compile_report.passed)
    check("compile qualification is JSON serializable", bool(json.dumps(compile_payload)))
    check("manual hardware check is not required for compile scope", compile_report.manual_checks_required is False)

    missing_report = target_machine_qualification.qualify_target_machine(
        scope="compile",
        env={"PATH": ""},
    )
    missing_payload = target_machine_qualification.to_dict(missing_report)
    missing_python = next(item for item in missing_report.prerequisites if item.name == "Python")
    check("missing target prerequisite is detected", missing_python.validation == "missing")
    check("missing target prerequisite fails qualification", missing_report.passed is False)
    check("failed qualification remains machine-readable", missing_payload["passed"] is False)

    hardware_items = target_machine_prerequisites.for_scope("hardware")
    hardware_names = {item.name for item in hardware_items}
    hardware_python = next(item for item in hardware_items if item.name == "Python")
    check("hardware scope includes Python", "Python" in hardware_names)
    check("hardware scope requires Python", target_machine_prerequisites.RequirementScope.HARDWARE in hardware_python.required_for)
    check("hardware scope includes PlatformIO", "PlatformIO Core" in hardware_names)
    check("hardware scope includes driver", "ESP32/USB driver" in hardware_names)
    check("hardware driver is explicitly manual", next(i for i in hardware_items if i.name == "ESP32/USB driver").kind is target_machine_prerequisites.PrerequisiteKind.DRIVER)

    print("RSD-21.4 target-machine-aware qualification checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
