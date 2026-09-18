"""RSD-21.2 target-machine prerequisite contract regression checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import target_machine_prerequisites


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    target_machine_prerequisites.validate_contract()
    items = target_machine_prerequisites.prerequisites()
    names = {item.name for item in items}

    check("prerequisite schema is stable", target_machine_prerequisites.SCHEMA == "antechkids.robostudio.target-machine-prerequisites")
    check("prerequisite schema version is artifact-closed", target_machine_prerequisites.SCHEMA_VERSION == 3)
    check("supported host OS policy is declared", target_machine_prerequisites.SUPPORTED_HOST_OS == "Windows 10/11 x64")
    check("PATH policy rejects host Python lookup", "must not require host Python" in target_machine_prerequisites.PATH_POLICY)
    check("Python is not a target prerequisite", "Python" not in names)
    check("PlatformIO Core is not a target prerequisite", "PlatformIO Core" not in names)
    check("ESP32/USB driver is a target prerequisite", "ESP32/USB driver" in names)
    check("driver is not packaged", next(i for i in items if i.name == "ESP32/USB driver").packaged is False)
    check("compile has no external prerequisite", target_machine_prerequisites.for_scope("compile") == ())
    hardware = target_machine_prerequisites.for_scope("hardware")
    check("hardware scope only requires external driver", {item.name for item in hardware} == {"ESP32/USB driver"})
    check("driver does not require PATH", hardware[0].path_required is False)
    check("portable Python is mandatory release payload", "Portable Python runtime" in target_machine_prerequisites.REQUIRED_BUNDLED_COMPONENTS)
    check("PlatformIO is mandatory release payload", "PlatformIO Core/runtime" in target_machine_prerequisites.REQUIRED_BUNDLED_COMPONENTS)
    check("global Python is forbidden as host prerequisite", "Global Python installation" in target_machine_prerequisites.FORBIDDEN_HOST_PREREQUISITES)
    check("global PlatformIO is forbidden as host prerequisite", "Global PlatformIO installation" in target_machine_prerequisites.FORBIDDEN_HOST_PREREQUISITES)
    check("developer virtualenv stays forbidden in production payload", "Developer virtual environment" in target_machine_prerequisites.FORBIDDEN_BUNDLED_PREREQUISITES)

    payload = target_machine_prerequisites.to_dict()
    check("machine-readable contract is JSON serializable", bool(json.dumps(payload)))
    check("host model is artifact closed", payload["host_model"] == "artifact-closed-copy-and-run")
    check("contract schema version is serialized", payload["schema_version"] == 3)
    check("supported host OS is serialized", payload["supported_host_os"] == "Windows 10/11 x64")
    check("release payload policy requires bundled Python", "Portable Python" in payload["release_payload_policy"])
    check("release payload policy requires bundled PlatformIO", "PlatformIO" in payload["release_payload_policy"])
    check("compile target prerequisites remain empty", not [item for item in payload["prerequisites"] if "compile" in item["required_for"]])

    print("RSD-21.2 target-machine prerequisite checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
