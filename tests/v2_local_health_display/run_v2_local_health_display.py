from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEALTH = ROOT / "robot-platform/main/src/Health"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
MAIN = ROOT / "robot-platform/main/main.ino"
PLATFORMIO = ROOT / "robot-platform/platformio.ini"

HARNESS = r"""
#include <cassert>
#include <cstring>
#include <string>
#include <vector>

#include "LocalHealthDisplayController.h"
#include "LocalHealthDisplayFormatter.h"

struct FakeHealthSource : IRobotHealthSource {
    RobotHealth value;
    int populateCalls = 0;

    void populate(RobotHealth& out) override {
        ++populateCalls;
        out = value;
    }
};

struct FakeDisplay : ILocalHealthDisplay {
    bool beginResult = true;
    bool renderResult = true;
    int beginCalls = 0;
    int renderCalls = 0;
    std::vector<std::string> last;

    bool begin() override {
        ++beginCalls;
        return beginResult;
    }

    bool render(const LocalHealthDisplayFrame& frame) override {
        ++renderCalls;
        last = {frame.line1, frame.line2, frame.line3, frame.line4};
        return renderResult;
    }
};

static RobotHealth normalHealth() {
    RobotHealth h;
    h.system.resetReason = ResetReason::POWER_ON;
    h.battery.voltage = 7.52f;
    h.battery.state = BatteryState::GOOD;
    h.motor.state = MotorSafetyState::SAFE;
    h.motor.enabled = false;
    h.network.connected = true;
    return h;
}

int main() {
    {
        FakeHealthSource source;
        source.value = normalHealth();
        RobotHealthService health(source);
        FakeDisplay display;
        LocalHealthDisplayController controller(health, display);

        controller.begin(0);
        assert(controller.displayAvailable());
        assert(display.beginCalls == 1);

        controller.update(0);
        assert(display.renderCalls == 1);
        assert(source.populateCalls == 1);
        assert(display.last[0] == "ANTECH ROBOT");
        assert(display.last[1] == "BAT GOOD 7.52V");
        assert(display.last[2] == "WiFi OK");
        assert(display.last[3] == "MOTOR SAFE");

        // Cadence is bounded: no health refresh or render before 500 ms.
        controller.update(499);
        assert(display.renderCalls == 1);
        assert(source.populateCalls == 1);

        controller.update(500);
        assert(display.renderCalls == 2);
        assert(source.populateCalls == 2);
    }

    {
        RobotHealth h = normalHealth();
        h.system.resetReason = ResetReason::BROWNOUT;
        h.battery.voltage = 6.30f;
        h.battery.state = BatteryState::CRITICAL;
        h.motor.state = MotorSafetyState::FAULT;
        h.motor.enabled = false;

        const auto frame = LocalHealthDisplayFormatter::format(h);
        assert(frame.lines[0] == "FAULT");
        assert(frame.lines[1] == "RESET BROWNOUT");
        assert(frame.lines[2] == "BAT CRITICAL 6.30V");
        assert(frame.lines[3] == "MOTOR LOCKED");
    }

    {
        // Missing OLED is optional and must not even refresh RobotHealth.
        FakeHealthSource source;
        source.value = normalHealth();
        RobotHealthService health(source);
        FakeDisplay display;
        display.beginResult = false;
        LocalHealthDisplayController controller(health, display);

        controller.begin(0);
        assert(!controller.displayAvailable());
        controller.update(1000);
        assert(display.renderCalls == 0);
        assert(source.populateCalls == 0);
    }

    {
        // Runtime display failure disables future attempts but does not throw
        // or mutate robot health/runtime state.
        FakeHealthSource source;
        source.value = normalHealth();
        RobotHealthService health(source);
        FakeDisplay display;
        display.renderResult = false;
        LocalHealthDisplayController controller(health, display);

        controller.begin(0);
        controller.update(0);
        assert(controller.renderAttempts() == 1);
        assert(controller.renderFailures() == 1);
        assert(!controller.displayAvailable());

        controller.update(1000);
        assert(controller.renderAttempts() == 1);
    }

    return 0;
}
"""

def test_real_local_display_cpp() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "local_health_display_test.cpp"
        exe = td / "local_health_display_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HEALTH), "-I", str(HAL),
            str(src),
            str(HEALTH / "LocalHealthDisplayController.cpp"),
            str(HEALTH / "LocalHealthDisplayFormatter.cpp"),
            str(HEALTH / "RobotHealthService.cpp"),
            str(HEALTH / "BatteryMonitor.cpp"),
            str(HEALTH / "ResetReasonService.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_runtime_consumes_robot_health_only() -> None:
    controller = (HEALTH / "LocalHealthDisplayController.cpp").read_text(encoding="utf-8")
    formatter = (HEALTH / "LocalHealthDisplayFormatter.cpp").read_text(encoding="utf-8")

    assert "_health.refresh()" in controller
    for forbidden in (
        "WiFi.", "analogRead", "readMask", "systemMCP23017",
        "systemBatteryMonitor", "systemMotorSafety", "systemStartArm",
        "RobotAPI::",
    ):
        assert forbidden not in controller, forbidden
        assert forbidden not in formatter, forbidden


def test_optional_runtime_integration() -> None:
    main = MAIN.read_text(encoding="utf-8")
    platform = (HEALTH / "LocalHealthDisplayPlatform.cpp").read_text(encoding="utf-8")

    assert "systemLocalHealthDisplay().begin(millis())" in main
    assert "systemLocalHealthDisplay().update(millis())" in main
    assert "runtime continues" in main
    assert "NullLocalHealthDisplay" in platform


def test_no_invented_oled_hardware_contract() -> None:
    platform = (HEALTH / "LocalHealthDisplayPlatform.cpp").read_text(encoding="utf-8")
    ini = PLATFORMIO.read_text(encoding="utf-8")
    combined = platform + "\n" + ini

    for invented in ("SSD1306", "SH1106", "0x3C", "0x3D", "Adafruit_SSD1306", "U8g2"):
        assert invented not in combined, invented


def main() -> int:
    test_real_local_display_cpp()
    print("PASS: real local health display formatter/controller and bounded cadence")
    test_runtime_consumes_robot_health_only()
    print("PASS: local display consumes RobotHealthService only")
    test_optional_runtime_integration()
    print("PASS: missing OLED is optional and runtime continues")
    test_no_invented_oled_hardware_contract()
    print("PASS: no OLED controller/address/library invented without hardware contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
