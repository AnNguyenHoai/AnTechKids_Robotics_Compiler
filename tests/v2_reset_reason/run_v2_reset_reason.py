from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEALTH = ROOT / "robot-platform/main/src/Health"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
MAIN = ROOT / "robot-platform/main/main.ino"

HARNESS = r"""
#include <cassert>
#include <cstring>

#include "ResetReasonService.h"
#include "MotorSafetyController.h"

struct FakeSource : IResetReasonSource {
    PlatformResetReason value = PlatformResetReason::OTHER;
    int reads = 0;
    PlatformResetReason readResetReason() override {
        ++reads;
        return value;
    }
};

struct FakeGate : IMotorSafetyGate {
    bool enabled = true;
    int writes = 0;
    void beginSafe() override { enabled = false; }
    void setDriverEnabled(bool value) override {
        enabled = value;
        ++writes;
    }
};

int main() {
    struct Case {
        PlatformResetReason raw;
        ResetReason normalized;
        const char* name;
    };

    const Case cases[] = {
        {PlatformResetReason::POWER_ON, ResetReason::POWER_ON, "POWER_ON"},
        {PlatformResetReason::SOFTWARE, ResetReason::SOFTWARE_RESET, "SOFTWARE_RESET"},
        {PlatformResetReason::WATCHDOG, ResetReason::WATCHDOG, "WATCHDOG"},
        {PlatformResetReason::BROWNOUT, ResetReason::BROWNOUT, "BROWNOUT"},
        {PlatformResetReason::PANIC, ResetReason::PANIC, "PANIC"},
        {PlatformResetReason::DEEP_SLEEP, ResetReason::DEEP_SLEEP, "DEEP_SLEEP"},
        {PlatformResetReason::OTHER, ResetReason::UNKNOWN, "UNKNOWN"},
    };

    for (const auto& tc : cases) {
        FakeSource source;
        source.value = tc.raw;
        ResetReasonService service(source);
        assert(!service.captured());
        service.capture();
        assert(service.captured());
        assert(service.reason() == tc.normalized);
        assert(std::strcmp(service.name(), tc.name) == 0);

        // Capture is one-shot: later source changes cannot overwrite boot context.
        source.value = PlatformResetReason::OTHER;
        service.capture();
        assert(source.reads == 1);
        assert(service.reason() == tc.normalized);
    }

    assert(ResetReasonService::isWatchdog(ResetReason::WATCHDOG));
    assert(!ResetReasonService::isWatchdog(ResetReason::BROWNOUT));

    // Watchdog reset context must remain SAFE and physically disabled.
    FakeGate gate;
    MotorSafetyController safety(gate, true);
    safety.begin();
    assert(safety.state() == MotorSafetyState::SAFE);
    assert(!gate.enabled);

    safety.setBootSafetyContext(MotorDisarmReason::WATCHDOG);
    assert(safety.state() == MotorSafetyState::SAFE);
    assert(safety.lastDisarmReason() == MotorDisarmReason::WATCHDOG);
    assert(!safety.isArmed());
    assert(!safety.isDriverEnabled());
    assert(!gate.enabled);

    // A fresh START-equivalent arm is required after watchdog reset.
    assert(safety.arm());
    assert(safety.isArmed());

    return 0;
}
"""

def test_real_reset_reason_cpp() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "reset_reason_test.cpp"
        exe = td / "reset_reason_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HEALTH), "-I", str(HAL),
            str(src),
            str(HEALTH / "ResetReasonService.cpp"),
            str(HAL / "MotorSafetyController.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_esp32_mapping_contract() -> None:
    source = (HEALTH / "Esp32ResetReasonSource.cpp").read_text(encoding="utf-8")
    required = {
        "ESP_RST_POWERON": "POWER_ON",
        "ESP_RST_SW": "SOFTWARE",
        "ESP_RST_INT_WDT": "WATCHDOG",
        "ESP_RST_TASK_WDT": "WATCHDOG",
        "ESP_RST_WDT": "WATCHDOG",
        "ESP_RST_BROWNOUT": "BROWNOUT",
        "ESP_RST_PANIC": "PANIC",
        "ESP_RST_DEEPSLEEP": "DEEP_SLEEP",
    }
    for token, mapped in required.items():
        assert token in source, token
        assert f"PlatformResetReason::{mapped}" in source, mapped
    assert "esp_reset_reason()" in source


def test_capture_order_and_watchdog_safety_context() -> None:
    main = MAIN.read_text(encoding="utf-8")
    capture = main.index("systemResetReasonService().capture();")
    robot_init = main.index("RobotAPI::Initialize();")
    start_begin = main.index("systemStartArm().begin(millis())")
    assert capture < robot_init < start_begin

    assert "ResetReasonService::isWatchdog(systemResetReasonService().reason())" in main
    assert "setBootSafetyContext(MotorDisarmReason::WATCHDOG)" in main


def test_health_ready_surface() -> None:
    header = (HEALTH / "ResetReasonService.h").read_text(encoding="utf-8")
    for name in (
        "POWER_ON",
        "SOFTWARE_RESET",
        "WATCHDOG",
        "BROWNOUT",
        "PANIC",
        "DEEP_SLEEP",
        "UNKNOWN",
    ):
        assert name in header
    assert "ResetReason reason() const" in header
    assert "const char* name() const" in header


def main() -> int:
    test_real_reset_reason_cpp()
    print("PASS: real ResetReasonService normalization and one-shot capture")
    test_esp32_mapping_contract()
    print("PASS: ESP32 reset reasons distinguish watchdog/brownout/panic/deep-sleep")
    test_capture_order_and_watchdog_safety_context()
    print("PASS: reset cause captured before runtime init; watchdog reboot remains SAFE")
    test_health_ready_surface()
    print("PASS: normalized reset reason is ready for RobotHealth integration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
