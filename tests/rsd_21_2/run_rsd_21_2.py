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
    check("prerequisite schema version is stable", target_machine_prerequisites.SCHEMA_VERSION == 2)
    check("supported host OS policy is declared", target_machine_prerequisites.SUPPORTED_HOST_OS == "Windows 10/11 x64")
    check("PATH policy is declared", "PATH" in target_machine_prerequisites.PATH_POLICY)
    check("Python is a target prerequisite", "Python" in names)
    check("PlatformIO Core is a target prerequisite", "PlatformIO Core" in names)
    check("ESP32/USB driver is a target prerequisite", "ESP32/USB driver" in names)
    check("Python is not packaged", next(i for i in items if i.name == "Python").packaged is False)
    check("PlatformIO is not packaged", next(i for i in items if i.name == "PlatformIO Core").packaged is False)
    check("driver is not packaged", next(i for i in items if i.name == "ESP32/USB driver").packaged is False)
    check("Python is required for compile", target_machine_prerequisites.for_scope("compile"))
    check("PlatformIO is required for hardware", target_machine_prerequisites.for_scope("hardware"))
    check("Python validation command is declared", next(i for i in items if i.name == "Python").command == ("python", "--version"))
    check("PlatformIO validation command is declared", next(i for i in items if i.name == "PlatformIO Core").command == ("pio", "--version"))
    check("Python setup policy is declared", bool(next(i for i in items if i.name == "Python").install_command))
    check("PlatformIO setup policy is declared", bool(next(i for i in items if i.name == "PlatformIO Core").install_command))
    check("driver does not require PATH", next(i for i in items if i.name == "ESP32/USB driver").path_required is False)
    check("forbidden bundled prerequisites are declared", set(target_machine_prerequisites.FORBIDDEN_BUNDLED_PREREQUISITES) >= {
        "Python installation",
        "PlatformIO installation",
        "Developer virtual environment",
        "Developer source repository",
    })

    payload = target_machine_prerequisites.to_dict()
    check("machine-readable contract is JSON serializable", bool(json.dumps(payload)))
    check("host model is target-machine-prerequisites", payload["host_model"] == "target-machine-prerequisites")
    check("contract schema version is serialized", payload["schema_version"] == 2)
    check("supported host OS is serialized", payload["supported_host_os"] == "Windows 10/11 x64")
    check("PATH policy is serialized", "PATH" in payload["path_policy"])
    check("prerequisite payload is non-empty", bool(payload["prerequisites"]))

    print("RSD-21.2 target-machine prerequisite checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
