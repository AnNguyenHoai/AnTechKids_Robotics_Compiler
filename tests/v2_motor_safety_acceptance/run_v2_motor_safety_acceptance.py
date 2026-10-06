from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
HEALTH = ROOT / "robot-platform/main/src/Health"
ROBOT = ROOT / "robot-platform/main/src/Services/Robot"
NETWORK = ROOT / "robot-platform/main/src/Communication/RobotNetworkService.cpp"
MAIN = ROOT / "robot-platform/main/main.ino"

HARNESS = r"""
#include <cassert>
#include <cstddef>
#include <initializer_list>
#include <vector>

#include "BatteryMonitor.h"
#include "BatterySafetyPolicy.h"
#include "MotorSafetyController.h"
#include "ResetReasonService.h"
#include "StartArmController.h"

struct FakeGate : IMotorSafetyGate {
    bool enabled = true;
    int enables = 0;
    int disables = 0;

    void beginSafe() override {
        enabled = false;
        ++disables;
    }

    void setDriverEnabled(bool value) override {
        enabled = value;
        if (value) ++enables;
        else ++disables;
    }
};

struct FakeStart : IStartArmInput {
    bool pressed = false;
    void begin() override {}
    bool isPressed() override { return pressed; }
};

struct FakeAdc : IBatteryAdcSource {
    std::vector<int> values;
    size_t index = 0;
    explicit FakeAdc(std::initializer_list<int> v) : values(v) {}
    int readRaw() override {
        assert(index < values.size());
        return values[index++];
    }
};

struct BatteryActions : IBatterySafetyActions {
    MotorSafetyController& safety;
    explicit BatteryActions(MotorSafetyController& s) : safety(s) {}

    void disarmForCriticalBattery() override {
        safety.disarm(MotorDisarmReason::LOW_BATTERY);
    }

    bool recoverLowBatteryFaultToSafe() override {
        return safety.recoverFaultToSafe(MotorDisarmReason::LOW_BATTERY);
    }
};

struct FakeResetSource : IResetReasonSource {
    PlatformResetReason value = PlatformResetReason::POWER_ON;
    PlatformResetReason readResetReason() override { return value; }
};

static BatteryMonitorConfig batteryConfig() {
    BatteryMonitorConfig c;
    c.adcMaxCount = 1000;
    c.adcReferenceVolts = 10.0f;
    c.calibrationFactor = 1.0f;
    c.lowThresholdVolts = 7.0f;
    c.criticalThresholdVolts = 6.0f;
    c.hysteresisVolts = 0.2f;
    c.sampleCount = 1;
    c.invalidLowRaw = 0;
    c.invalidHighRaw = 1000;
    c.calibrationValid = true;
    return c;
}

static void stablePress(StartArmController& start, FakeStart& input, uint32_t at) {
    input.pressed = true;
    assert(!start.update(at));
    assert(start.update(at + StartArmController::DEBOUNCE_MS));
}

int main() {
    FakeGate gate;
    MotorSafetyController safety(gate, true);

    // Required: BOOT -> SAFE and physical driver disabled.
    assert(safety.state() == MotorSafetyState::BOOT);
    assert(!safety.isArmed());
    safety.begin();
    assert(safety.state() == MotorSafetyState::SAFE);
    assert(!gate.enabled);

    // Required: non-zero motion before START is blocked.
    assert(!safety.allowPhysicalOutput(35, 35));
    assert(!gate.enabled);

    FakeStart input;
    StartArmController start(input, safety);
    start.begin(0);
    start.onSystemReady(100);

    // Required: START -> ARMED.
    stablePress(start, input, 110);
    assert(safety.state() == MotorSafetyState::ARMED);
    assert(safety.isArmed());
    assert(gate.enabled);

    // Armed motion can enter RUNNING.
    assert(safety.allowPhysicalOutput(50, -50));
    assert(safety.state() == MotorSafetyState::RUNNING);

    // Required: OTA -> SAFE, output blocked afterwards.
    safety.disarm(MotorDisarmReason::OTA);
    assert(safety.state() == MotorSafetyState::SAFE);
    assert(!gate.enabled);
    assert(!safety.allowPhysicalOutput(50, 50));

    // Re-arm needs a new release -> press edge.
    input.pressed = false;
    assert(!start.update(200));
    assert(!start.update(200 + StartArmController::DEBOUNCE_MS));
    stablePress(start, input, 250);
    assert(safety.isArmed());

    // Required critical-battery semantics:
    // CRITICAL -> FAULT/STBY LOW, hysteretic recovery -> SAFE, never auto-arm.
    FakeAdc adc{590, 610, 621};
    BatteryMonitor monitor(adc, batteryConfig());
    BatteryActions actions(safety);
    BatterySafetyPolicy battery(monitor, actions);

    assert(battery.update(0) == BatterySafetyEvent::CRITICAL_DISARMED);
    assert(safety.state() == MotorSafetyState::FAULT);
    assert(!safety.isArmed());
    assert(!gate.enabled);
    assert(!safety.allowPhysicalOutput(80, 80));

    // Still below CRITICAL+hysteresis.
    assert(battery.update(250) == BatterySafetyEvent::NONE);
    assert(safety.state() == MotorSafetyState::FAULT);

    // Above recovery boundary: FAULT -> SAFE, but no automatic ARM.
    assert(battery.update(500) == BatterySafetyEvent::RECOVERED_SAFE);
    assert(safety.state() == MotorSafetyState::SAFE);
    assert(!safety.isArmed());
    assert(!gate.enabled);

    // Required generic fault is physically safe and cannot direct-arm.
    assert(safety.arm());
    safety.disarm(MotorDisarmReason::FATAL_PLATFORM_FAULT);
    assert(safety.state() == MotorSafetyState::FAULT);
    assert(!gate.enabled);
    assert(!safety.arm());
    assert(!safety.allowPhysicalOutput(100, 100));

    // Required reset/watchdog reboot context -> SAFE, driver LOW, fresh START needed.
    MotorSafetyController rebooted(gate, true);
    rebooted.begin();
    FakeResetSource resetSource;
    resetSource.value = PlatformResetReason::WATCHDOG;
    ResetReasonService reset(resetSource);
    reset.capture();
    assert(reset.reason() == ResetReason::WATCHDOG);
    rebooted.setBootSafetyContext(MotorDisarmReason::WATCHDOG);
    assert(rebooted.state() == MotorSafetyState::SAFE);
    assert(!rebooted.isArmed());
    assert(!gate.enabled);
    assert(!rebooted.allowPhysicalOutput(100, 100));

    return 0;
}
"""


def test_end_to_end_real_cpp_contract() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "motor_safety_contract.cpp"
        exe = td / "motor_safety_contract"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HAL), "-I", str(HEALTH),
            str(src),
            str(HAL / "MotorSafetyController.cpp"),
            str(HAL / "StartArmController.cpp"),
            str(HEALTH / "BatteryMonitor.cpp"),
            str(HEALTH / "BatterySafetyPolicy.cpp"),
            str(HEALTH / "ResetReasonService.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_no_nonzero_physical_pwm_without_safety_gate() -> None:
    api = (ROBOT / "RobotAPI.cpp").read_text(encoding="utf-8")
    raw_start = api.index("static void _setMotorsRaw")
    raw_end = api.index("// H23-A ownership boundary", raw_start)
    raw = api[raw_start:raw_end]

    gate = raw.index("systemMotorSafety().allowPhysicalOutput")
    normal_pwm = raw.index("ledcWrite(MOTOR_L_IN1_PIN, leftPWM)")
    assert gate < normal_pwm

    blocked = raw[:raw.index("// ---- DIAGNOSTIC")]
    for pin in (
        "MOTOR_L_IN1_PIN",
        "MOTOR_L_IN2_PIN",
        "MOTOR_R_IN3_PIN",
        "MOTOR_R_IN4_PIN",
    ):
        assert f"ledcWrite({pin}, 0)" in blocked

    all_pwm = [i for i in range(len(api)) if api.startswith("ledcWrite(MOTOR_", i)]
    assert all_pwm
    assert all(raw_start <= i < raw_end for i in all_pwm)


def test_system_events_route_through_fail_safe_boundary() -> None:
    network = NETWORK.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    internal = (ROBOT / "RobotMotorSafetyInternal.h").read_text(encoding="utf-8")
    api_h = (ROBOT / "RobotAPI.h").read_text(encoding="utf-8")

    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::OTA)" in network
    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::REBOOT)" in network
    assert main.count("MotorDisarmReason::FATAL_PLATFORM_FAULT") >= 3

    assert "clear motor PWM/state first" in internal
    assert "MotorSafety" not in api_h
    assert " arm(" not in api_h.lower()


def test_approved_arm_owner_is_start_only() -> None:
    start = (HAL / "StartArmController.cpp").read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    network = NETWORK.read_text(encoding="utf-8")

    assert "_motorSafety.arm()" in start
    assert ".arm()" not in main
    assert ".arm()" not in network


def main() -> int:
    test_end_to_end_real_cpp_contract()
    print("PASS: integrated real C++ BOOT/START/OTA/battery/fault/reset safety contract")
    test_no_nonzero_physical_pwm_without_safety_gate()
    print("PASS: no physical motor PWM path bypasses MotorSafety")
    test_system_events_route_through_fail_safe_boundary()
    print("PASS: OTA/reboot/fatal lifecycle events route through fail-safe disarm")
    test_approved_arm_owner_is_start_only()
    print("PASS: START controller remains the only approved production arm owner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
