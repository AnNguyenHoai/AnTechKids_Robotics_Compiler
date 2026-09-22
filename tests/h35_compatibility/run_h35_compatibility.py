#!/usr/bin/env python3
"""Regression gate for H35 Compatibility / Upgrade Policy."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ROBOSTUDIO = ROOT / "robostudio"
if str(ROBOSTUDIO) not in sys.path:
    sys.path.insert(0, str(ROBOSTUDIO))

from domain.compatibility import (  # noqa: E402
    CURRENT_COMPILER_GENERATION,
    CURRENT_FIRMWARE_GENERATION,
    LEGACY_UNVERSIONED_FIRMWARE_GENERATION,
    normalize_firmware_generation,
    ota_compatibility_error,
)
from services.robot_discovery_service import (  # noqa: E402
    validate_robot_info,
    serialize_robot_info,
)

EVIDENCE = ROOT / ".build" / "h35" / "compatibility-report.json"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_value_error(name: str, value: object) -> None:
    try:
        normalize_firmware_generation(value)
    except ValueError:
        print(f"PASS: {name}")
        return
    raise AssertionError(name)


def identity_payload(**overrides):
    payload = {
        "protocol": "antechkids.robot.v1",
        "schema_version": 1,
        "compatibility_generation": CURRENT_FIRMWARE_GENERATION,
        "device_id": "robot-001122334455",
        "name": "AnTechKids Robot 334455",
        "hostname": "robot-334455",
        "ip": "192.168.1.22",
        "target": "esp32",
        "firmware": "0.1.1",
        "robot_ready": True,
        "network_ready": True,
        "ready": True,
        "ota": True,
        "capabilities": {"motor": True, "line_sensor": True},
    }
    payload.update(overrides)
    return payload


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "compatibility_policy.py")],
        cwd=ROOT,
        text=True,
    )
    check("H35 checker exits successfully", result.returncode == 0)
    check("H35 evidence is emitted", EVIDENCE.is_file())
    report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    check("H35 evidence schema is stable", report.get("schema_version") == 1)
    check("H35 evidence status is PASS", report.get("status") == "PASS")
    check("H35 has zero policy errors", report.get("errors") == [])
    check("current release is governed", report.get("release") == "0.1.1")
    check("current compiler generation is 1", CURRENT_COMPILER_GENERATION == 1)
    check("current firmware generation is 1", CURRENT_FIRMWARE_GENERATION == 1)

    check(
        "legacy unversioned firmware maps only to explicit generation 0",
        normalize_firmware_generation(None) == LEGACY_UNVERSIONED_FIRMWARE_GENERATION == 0,
    )
    check("current firmware generation is accepted", normalize_firmware_generation(1) == 1)
    check("legacy firmware is an allowed OTA upgrade source", ota_compatibility_error(0) is None)
    check("current firmware is an allowed OTA source", ota_compatibility_error(1) is None)
    check("future firmware pair fails closed", ota_compatibility_error(2) is not None)
    expect_value_error("future discovery generation is rejected", 2)
    expect_value_error("negative discovery generation is rejected", -1)
    expect_value_error("boolean discovery generation is rejected", True)
    expect_value_error("string discovery generation is rejected", "1")

    current = validate_robot_info(identity_payload())
    check("current robot identity carries generation 1", current.compatibility_generation == 1)
    serialized = serialize_robot_info(current)
    check("registry serialization preserves compatibility generation", serialized.get("compatibility_generation") == 1)

    legacy_payload = identity_payload()
    legacy_payload.pop("compatibility_generation")
    legacy = validate_robot_info(legacy_payload)
    check("pre-H35 robot remains discoverable as explicit legacy generation", legacy.compatibility_generation == 0)

    try:
        validate_robot_info(identity_payload(compatibility_generation=2))
    except ValueError as exc:
        check("future robot is rejected at discovery boundary", "unsupported robot compatibility generation" in str(exc))
    else:
        raise AssertionError("future robot is rejected at discovery boundary")

    checks = report.get("checks", [])
    check("compatibility evidence contains contract checks", len(checks) >= 20)
    check("every H35 evidence check passed", all(row.get("pass") for row in checks))

    print("H35 Compatibility / Upgrade Policy regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
