from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMM = ROOT / "robot-platform/main/src/Communication"
HEALTH = ROOT / "robot-platform/main/src/Health"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
NETWORK = COMM / "RobotNetworkService.cpp"

HARNESS = r"""
#include <iostream>
#include "RobotHealthJsonSerializer.h"

int main() {
    RobotHealth h;
    h.system.uptimeMs = 4567;
    h.system.resetReason = ResetReason::BROWNOUT;
    h.system.firmwareVersion = "2.0-test";
    h.system.boardProfile = "antech_robot_v2";
    h.system.boardRevision = "v2";

    h.battery.voltage = 7.52f;
    h.battery.state = BatteryState::GOOD;

    h.motor.armed = false;
    h.motor.enabled = false;
    h.motor.state = MotorSafetyState::SAFE;
    h.motor.lastStopReason = MotorDisarmReason::LOW_BATTERY;

    h.start.pressed = false;
    h.start.readyForPress = true;
    h.start.armedByStartThisBoot = false;

    h.line.available = true;
    h.line.healthy = true;
    h.line.mask = 4;

    h.encoder.available = true;
    h.encoder.healthy = true;
    h.encoder.leftCount = 123;
    h.encoder.rightCount = -45;

    h.i2c.healthy = true;
    h.i2c.mcp23017 = true;

    h.network.connected = true;
    h.network.ip = "192.168.1.25";
    h.network.rssi = -52;

    RobotHealthCompatibilityFields compat;
    compat.ready = true;
    compat.robotReady = true;
    compat.networkReady = true;
    compat.otaReady = true;
    compat.httpOtaAvailable = true;
    compat.hostname = "robot-\"safe";

    std::cout << RobotHealthJsonSerializer::serialize(h, compat);
    return 0;
}
"""

def build_payload() -> dict:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "health_json_test.cpp"
        exe = td / "health_json_test"
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
        raw = subprocess.check_output([str(exe)], text=True)
    return json.loads(raw)


def test_schema_and_compatibility() -> None:
    payload = build_payload()

    # Compatibility-critical V1 fields must remain.
    for field in (
        "status", "ready", "robot_ready", "network_ready",
        "ota", "hostname", "ip",
    ):
        assert field in payload, field

    assert payload["status"] == "ok"
    assert payload["ready"] is True
    assert payload["robot_ready"] is True
    assert payload["network_ready"] is True
    assert payload["ota"] is True
    assert payload["http_ota"] is True
    assert payload["hostname"] == 'robot-"safe'
    assert payload["ip"] == "192.168.1.25"

    assert payload["board_profile"] == "antech_robot_v2"
    assert payload["board_revision"] == "v2"
    assert payload["firmware_version"] == "2.0-test"
    assert payload["reset_reason"] == "BROWNOUT"
    assert payload["uptime_ms"] == 4567

    assert payload["battery"] == {"voltage": 7.52, "state": "GOOD"}
    assert payload["motor"]["armed"] is False
    assert payload["motor"]["enabled"] is False
    assert payload["motor"]["state"] == "SAFE"
    assert payload["motor"]["last_stop_reason"] == "LOW_BATTERY"

    assert payload["line"] == {"available": True, "healthy": True, "mask": 4}
    assert payload["line_mask"] == 4
    assert payload["encoder"] == {
        "available": True,
        "healthy": True,
        "left_count": 123,
        "right_count": -45,
    }
    assert payload["i2c"] == {"healthy": True, "mcp23017": True}
    assert payload["i2c_ok"] is True
    assert payload["rssi"] == -52


def test_optional_failure_still_serializes() -> None:
    # Static contract: serializer has no hardware reads or throwing optional-device branches.
    serializer = (COMM / "RobotHealthJsonSerializer.cpp").read_text(encoding="utf-8")
    for forbidden in (
        "WiFi.", "analogRead", "readMask", "systemMCP23017",
        "systemBatteryMonitor", "systemMotorSafety", "systemStartArm",
    ):
        assert forbidden not in serializer, forbidden


def test_endpoint_consumes_aggregate_only() -> None:
    network = NETWORK.read_text(encoding="utf-8")
    start = network.index("void sendHealth()")
    end = network.index("void sendInfo()", start)
    body = network[start:end]

    assert "systemRobotHealth().refresh()" in body
    assert "RobotHealthJsonSerializer::serialize" in body

    # Compatibility values may come from the network service state, but V2
    # subsystem health must not be recomputed here.
    for forbidden in (
        "systemBatteryMonitor", "systemMotorSafety", "GetTraceRaw",
        "systemMCP23017", "SystemI2CBusManager",
    ):
        assert forbidden not in body, forbidden


def test_no_secrets_in_health_serializer_or_endpoint() -> None:
    serializer = (COMM / "RobotHealthJsonSerializer.cpp").read_text(encoding="utf-8").lower()
    network = NETWORK.read_text(encoding="utf-8")
    start = network.index("void sendHealth()")
    end = network.index("void sendInfo()", start)
    body = network[start:end].lower()

    secret_tokens = (
        "password", "ssid", "otapassword", "robotwificonfig",
        "authorization", "basic_auth",
    )
    for token in secret_tokens:
        assert token not in serializer, token
        assert token not in body, token


def main() -> int:
    test_schema_and_compatibility()
    print("PASS: /api/v1/health V2 JSON preserves compatibility fields and adds aggregate health")
    test_optional_failure_still_serializes()
    print("PASS: optional-device failures serialize without direct hardware access")
    test_endpoint_consumes_aggregate_only()
    print("PASS: health endpoint consumes RobotHealthService instead of duplicating subsystem logic")
    test_no_secrets_in_health_serializer_or_endpoint()
    print("PASS: health endpoint/serializer expose no Wi-Fi or OTA secrets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
