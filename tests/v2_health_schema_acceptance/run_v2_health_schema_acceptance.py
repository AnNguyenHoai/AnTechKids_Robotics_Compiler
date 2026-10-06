from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMM = ROOT / "robot-platform/main/src/Communication"
HEALTH = ROOT / "robot-platform/main/src/Health"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
NETWORK = COMM / "RobotNetworkService.cpp"
CLIENT = ROOT / "robostudio/services/robot_health_service.py"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "robostudio"))
from robostudio.services.robot_health_service import (
    RobotHealthPayloadError,
    validate_health_payload,
)

HARNESS = r"""
#include <iostream>
#include <string>

#include "RobotHealthJsonSerializer.h"

static RobotHealthCompatibilityFields compat() {
    RobotHealthCompatibilityFields c;
    c.ready = true;
    c.robotReady = true;
    c.networkReady = true;
    c.otaReady = true;
    c.httpOtaAvailable = true;
    c.hostname = "robot-\"health\\node";
    return c;
}

static RobotHealth normal() {
    RobotHealth h;
    h.system.uptimeMs = 98765;
    h.system.resetReason = ResetReason::WATCHDOG;
    h.system.firmwareVersion = "2.0\nrelease";
    h.system.boardProfile = "antech_robot_v2";
    h.system.boardRevision = std::string("v2\tctrl") + char(1);

    h.battery.voltage = 7.61f;
    h.battery.state = BatteryState::GOOD;

    h.motor.armed = true;
    h.motor.enabled = true;
    h.motor.state = MotorSafetyState::ARMED;
    h.motor.lastStopReason = MotorDisarmReason::WATCHDOG;

    h.start.pressed = false;
    h.start.readyForPress = false;
    h.start.armedByStartThisBoot = true;

    h.line.available = true;
    h.line.healthy = true;
    h.line.mask = 0x04;

    h.encoder.available = true;
    h.encoder.healthy = true;
    h.encoder.leftCount = 111;
    h.encoder.rightCount = -222;

    h.i2c.healthy = true;
    h.i2c.mcp23017 = true;

    h.network.connected = true;
    h.network.ip = "192.168.4.25";
    h.network.rssi = -48;
    return h;
}

static RobotHealth degraded() {
    RobotHealth h = normal();

    // Production calibration can intentionally be unresolved: INVALID is a
    // valid health state, not a JSON/schema failure.
    h.battery.voltage = 0.0f;
    h.battery.state = BatteryState::INVALID;

    // Optional devices disabled/unavailable must remain representable.
    h.line.available = false;
    h.line.healthy = false;
    h.line.mask = 0;
    h.encoder.available = false;
    h.encoder.healthy = false;
    h.encoder.leftCount = 0;
    h.encoder.rightCount = 0;

    // Bus/MCP degradation must still serialize a complete response.
    h.i2c.healthy = false;
    h.i2c.mcp23017 = false;

    h.network.connected = false;
    h.network.ip = "";
    h.network.rssi = 0;

    h.motor.armed = false;
    h.motor.enabled = false;
    h.motor.state = MotorSafetyState::FAULT;
    h.motor.lastStopReason = MotorDisarmReason::FATAL_PLATFORM_FAULT;
    return h;
}

int main(int argc, char** argv) {
    const bool useDegraded = argc > 1 && std::string(argv[1]) == "degraded";
    std::cout << RobotHealthJsonSerializer::serialize(
        useDegraded ? degraded() : normal(),
        compat()
    );
    return 0;
}
"""

COMPAT = {
    "status", "ready", "robot_ready", "network_ready",
    "ota", "http_ota", "hostname", "ip",
}

V2_TOP = {
    "uptime_ms", "firmware_version", "board_profile", "board_revision",
    "reset_reason", "battery", "motor", "start", "line", "line_mask",
    "encoder", "i2c", "i2c_ok", "rssi",
}


def build(mode: str | None = None) -> dict:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "health_schema_acceptance.cpp"
        exe = td / "health_schema_acceptance"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(COMM), "-I", str(HEALTH), "-I", str(HAL),
            str(src),
            str(COMM / "RobotHealthJsonSerializer.cpp"),
            str(HEALTH / "RobotHealthService.cpp"),
            str(HEALTH / "BatteryMonitor.cpp"),
            str(HEALTH / "ResetReasonService.cpp"),
            "-o", str(exe),
        ], check=True)
        args = [str(exe)]
        if mode:
            args.append(mode)
        raw = subprocess.check_output(args, text=True)
    return json.loads(raw)


def test_backward_compatibility_and_v2_schema() -> None:
    payload = build()
    assert COMPAT <= payload.keys(), COMPAT - payload.keys()
    assert V2_TOP <= payload.keys(), V2_TOP - payload.keys()

    assert payload["status"] == "ok"
    assert payload["hostname"] == 'robot-"health\\node'
    assert payload["firmware_version"] == "2.0\nrelease"
    assert payload["board_profile"] == "antech_robot_v2"
    assert payload["board_revision"] == "v2\tctrl\x01"
    assert payload["line_mask"] == payload["line"]["mask"]
    assert payload["i2c_ok"] == payload["i2c"]["healthy"]

    assert set(payload["battery"]) == {"voltage", "state"}
    assert set(payload["motor"]) == {"armed", "enabled", "state", "last_stop_reason"}
    assert set(payload["start"]) == {"pressed", "ready_for_press", "armed_by_start_this_boot"}
    assert set(payload["line"]) == {"available", "healthy", "mask"}
    assert set(payload["encoder"]) == {"available", "healthy", "left_count", "right_count"}
    assert set(payload["i2c"]) == {"healthy", "mcp23017"}


def test_degraded_optional_devices_do_not_corrupt_json() -> None:
    payload = build("degraded")
    assert payload["status"] == "ok"
    assert payload["battery"] == {"voltage": 0.0, "state": "INVALID"}
    assert payload["line"] == {"available": False, "healthy": False, "mask": 0}
    assert payload["encoder"] == {
        "available": False,
        "healthy": False,
        "left_count": 0,
        "right_count": 0,
    }
    assert payload["i2c"] == {"healthy": False, "mcp23017": False}
    assert payload["motor"]["state"] == "FAULT"
    assert payload["network_ready"] is True  # compatibility runtime flag is independent
    assert payload["ip"] == ""
    assert payload["rssi"] == 0

    # RoboStudio validator must accept a complete degraded health payload.
    validate_health_payload(payload)


def _expect_payload_error(payload: dict, label: str) -> None:
    try:
        validate_health_payload(payload)
    except RobotHealthPayloadError:
        return
    raise AssertionError(f"consumer accepted malformed/incompatible payload: {label}")


def test_consumer_rejects_missing_required_v2_fields() -> None:
    payload = build()

    for field in sorted(COMPAT | V2_TOP):
        malformed = json.loads(json.dumps(payload))
        del malformed[field]
        _expect_payload_error(malformed, f"missing top-level field {field}")

    required_nested = {
        "battery": ("voltage", "state"),
        "motor": ("armed", "enabled", "state", "last_stop_reason"),
        "start": ("pressed", "ready_for_press", "armed_by_start_this_boot"),
        "line": ("available", "healthy", "mask"),
        "encoder": ("available", "healthy", "left_count", "right_count"),
        "i2c": ("healthy", "mcp23017"),
    }
    for obj, fields in required_nested.items():
        for field in fields:
            malformed = json.loads(json.dumps(payload))
            del malformed[obj][field]
            _expect_payload_error(malformed, f"missing nested field {obj}.{field}")

    malformed = json.loads(json.dumps(payload))
    malformed["line_mask"] = payload["line"]["mask"] ^ 0x01
    _expect_payload_error(malformed, "line_mask alias mismatch")

    malformed = json.loads(json.dumps(payload))
    malformed["i2c_ok"] = not payload["i2c"]["healthy"]
    _expect_payload_error(malformed, "i2c_ok alias mismatch")


def test_endpoint_is_aggregate_only_and_secret_free() -> None:
    serializer = (COMM / "RobotHealthJsonSerializer.cpp").read_text(encoding="utf-8").lower()
    network = NETWORK.read_text(encoding="utf-8")
    start = network.index("void sendHealth()")
    end = network.index("void sendInfo()", start)
    body = network[start:end]
    low = body.lower()

    assert "systemRobotHealth().refresh()" in body
    assert "RobotHealthJsonSerializer::serialize" in body

    forbidden_hardware = (
        "systemBatteryMonitor", "systemMotorSafety", "GetTraceRaw",
        "systemMCP23017", "SystemI2CBusManager", "analogRead",
    )
    for token in forbidden_hardware:
        assert token not in body, token

    secret_tokens = (
        "password", "ssid", "otapassword", "robotwificonfig",
        "authorization", "basic_auth", "httpotauser",
    )
    for token in secret_tokens:
        assert token not in serializer, token
        assert token not in low, token


def test_schema_has_no_hardware_dependent_omission() -> None:
    normal = build()
    degraded = build("degraded")
    assert set(normal.keys()) == set(degraded.keys())
    for nested in ("battery", "motor", "start", "line", "encoder", "i2c"):
        assert set(normal[nested].keys()) == set(degraded[nested].keys())


def main() -> int:
    test_backward_compatibility_and_v2_schema()
    print("PASS: compatibility fields, aliases, mandatory V2 schema and control-character escaping are stable")
    test_degraded_optional_devices_do_not_corrupt_json()
    print("PASS: invalid/unavailable optional devices serialize valid complete JSON")
    test_consumer_rejects_missing_required_v2_fields()
    print("PASS: RoboStudio rejects malformed/incomplete health schema rather than inventing defaults")
    test_endpoint_is_aggregate_only_and_secret_free()
    print("PASS: health endpoint remains aggregate-only and secret-free")
    test_schema_has_no_hardware_dependent_omission()
    print("PASS: normal and degraded snapshots expose the same schema shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
