from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEALTH = ROOT / "robot-platform/main/src/Health"
ROBOT = ROOT / "robot-platform/main/src/Services/Robot"
COMM = ROOT / "robot-platform/main/src/Communication"
SERIAL = COMM / "SerialCommandHandler.cpp"

HARNESS = r"""
#include <cassert>
#include <cstring>
#include "RobotHealthService.h"

struct FakeSource : IRobotHealthSource {
    int calls = 0;

    void populate(RobotHealth& h) override {
        ++calls;
        h.system.uptimeMs = 1234;
        h.system.resetReason = ResetReason::BROWNOUT;
        h.system.firmwareVersion = "fw-test";
        h.system.boardProfile = "antech_robot_v2";
        h.system.boardRevision = "v2";

        h.battery.voltage = 7.42f;
        h.battery.state = BatteryState::LOW;

        h.motor.armed = false;
        h.motor.enabled = false;
        h.motor.state = MotorSafetyState::SAFE;
        h.motor.lastStopReason = MotorDisarmReason::LOW_BATTERY;

        h.start.pressed = false;
        h.start.readyForPress = true;
        h.start.armedByStartThisBoot = false;

        h.line.available = true;
        h.line.healthy = true;
        h.line.mask = 0x04;

        h.encoder.available = true;
        h.encoder.healthy = true;
        h.encoder.leftCount = 123;
        h.encoder.rightCount = -45;

        h.i2c.healthy = true;
        h.i2c.mcp23017 = true;

        h.network.connected = true;
        h.network.ip = "192.168.1.10";
        h.network.rssi = -52;
    }
};

int main() {
    FakeSource source;
    RobotHealthService service(source);

    const RobotHealth& h = service.refresh();
    assert(source.calls == 1);
    assert(h.system.uptimeMs == 1234);
    assert(h.system.resetReason == ResetReason::BROWNOUT);
    assert(std::strcmp(h.system.boardProfile, "antech_robot_v2") == 0);
    assert(h.battery.state == BatteryState::LOW);
    assert(h.motor.state == MotorSafetyState::SAFE);
    assert(h.motor.lastStopReason == MotorDisarmReason::LOW_BATTERY);
    assert(h.start.readyForPress);
    assert(h.line.mask == 0x04);
    assert(h.encoder.available && h.encoder.healthy);
    assert(h.encoder.leftCount == 123);
    assert(h.encoder.rightCount == -45);
    assert(h.i2c.healthy && h.i2c.mcp23017);
    assert(h.network.connected && h.network.rssi == -52);

    assert(std::strcmp(RobotHealthService::motorStateName(MotorSafetyState::FAULT), "FAULT") == 0);
    assert(std::strcmp(RobotHealthService::motorStopReasonName(MotorDisarmReason::OTA), "OTA") == 0);

    return 0;
}
"""

def test_real_health_service_cpp() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "robot_health_test.cpp"
        exe = td / "robot_health_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HEALTH), "-I", str(ROOT / "robot-platform/main/src/HardwareAbstraction"),
            str(src), str(HEALTH / "RobotHealthService.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_minimum_model_contract() -> None:
    model = (HEALTH / "RobotHealth.h").read_text(encoding="utf-8")
    for field in (
        "uptimeMs", "resetReason", "firmwareVersion", "boardProfile", "boardRevision",
        "voltage", "BatteryState state",
        "armed", "enabled", "lastStopReason",
        "RobotHealthLine", "mask",
        "RobotHealthEncoder", "leftCount", "rightCount",
        "RobotHealthI2C", "mcp23017",
        "RobotHealthNetwork", "connected", "ip", "rssi",
    ):
        assert field in model, field


def test_platform_source_is_read_only_aggregate() -> None:
    source = (HEALTH / "RobotHealthPlatformSource.cpp").read_text(encoding="utf-8")
    assert "systemBatteryMonitor().voltage()" in source
    assert "systemBatteryMonitor().state()" in source
    assert ".sample()" not in source
    assert "GetTraceRaw" not in source
    assert "readMask" not in source
    assert "systemMCP23017().begin" not in source
    assert "RobotHealthInputsInternal::lineMask()" in source
    assert "RobotNetworkService::ipAddress()" in source
    assert "RobotNetworkService::rssi()" in source


def test_line_encoder_internal_health_bridge() -> None:
    api = (ROBOT / "RobotAPI.cpp").read_text(encoding="utf-8")
    bridge = (ROBOT / "RobotHealthInputsInternal.h").read_text(encoding="utf-8")
    assert "g_leftEncoderReady = leftEncoder.begin()" in api
    assert "g_rightEncoderReady = rightEncoder.begin()" in api
    assert "g_lineSensorBank.healthy()" in api
    assert "g_lineSensorBank.lastMask()" in api
    assert "leftEncoder.getCount()" in api
    assert "rightEncoder.getCount()" in api
    assert "RobotHealthInputsInternal" in bridge

    public_api = (ROBOT / "RobotAPI.h").read_text(encoding="utf-8")
    assert "RobotHealthInputsInternal" not in public_api


def test_serial_and_http_consume_same_health_model() -> None:
    serial = SERIAL.read_text(encoding="utf-8")
    network = (COMM / "RobotNetworkService.cpp").read_text(encoding="utf-8")

    status_start = serial.index('else if (input.startsWith("robot status"))')
    status_end = serial.index("// ---------- Ultrasonic Diagnostics ----------", status_start)
    status = serial[status_start:status_end]
    assert "systemRobotHealth().refresh()" in status
    assert "health.battery" in status
    assert "health.motor" in status
    assert "health.line" in status
    assert "health.encoder" in status
    assert "health.i2c" in status
    assert "health.network" in status

    # V2-NET-001 migration is now complete: HTTP and Serial must consume the
    # same RobotHealth aggregate rather than duplicate subsystem health logic.
    health_start = network.index("void sendHealth()")
    health_end = network.index("void sendInfo()", health_start)
    health = network[health_start:health_end]
    assert "systemRobotHealth().refresh()" in health
    assert "RobotHealthJsonSerializer::serialize" in health


def main() -> int:
    test_real_health_service_cpp()
    print("PASS: real RobotHealthService aggregate model with injected source")
    test_minimum_model_contract()
    print("PASS: RobotHealth minimum V2 model fields")
    test_platform_source_is_read_only_aggregate()
    print("PASS: platform health source is read-only and side-effect free")
    test_line_encoder_internal_health_bridge()
    print("PASS: Line/Encoder health bridged internally without public API leakage")
    test_serial_and_http_consume_same_health_model()
    print("PASS: Serial and HTTP consume the same RobotHealth aggregate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
