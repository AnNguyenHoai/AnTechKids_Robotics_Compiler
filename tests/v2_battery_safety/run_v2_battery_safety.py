from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEALTH = ROOT / "robot-platform/main/src/Health"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
API = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
MAIN = ROOT / "robot-platform/main/main.ino"

HARNESS = r"""
#include <cassert>
#include <cstddef>
#include <initializer_list>
#include <vector>

#include "BatteryMonitor.h"
#include "BatterySafetyPolicy.h"
#include "MotorSafetyController.h"

struct FakeAdc : IBatteryAdcSource {
    std::vector<int> values;
    size_t index = 0;
    explicit FakeAdc(std::initializer_list<int> v) : values(v) {}
    int readRaw() override {
        assert(index < values.size());
        return values[index++];
    }
};

struct FakeGate : IMotorSafetyGate {
    bool enabled = true;
    void beginSafe() override { enabled = false; }
    void setDriverEnabled(bool value) override { enabled = value; }
};

struct Actions : IBatterySafetyActions {
    MotorSafetyController& motor;
    int disarms = 0;
    int recoveries = 0;

    explicit Actions(MotorSafetyController& m) : motor(m) {}

    void disarmForCriticalBattery() override {
        ++disarms;
        motor.disarm(MotorDisarmReason::LOW_BATTERY);
    }

    bool recoverLowBatteryFaultToSafe() override {
        ++recoveries;
        return motor.recoverFaultToSafe(MotorDisarmReason::LOW_BATTERY);
    }
};

static BatteryMonitorConfig cfg() {
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

int main() {
    {
        FakeAdc adc{800, 690, 590, 610, 621, 690};
        BatteryMonitor monitor(adc, cfg());
        FakeGate gate;
        MotorSafetyController motor(gate, true);
        motor.begin();
        assert(motor.arm());
        Actions actions(motor);
        BatterySafetyPolicy policy(monitor, actions);

        assert(policy.update(0) == BatterySafetyEvent::NONE);
        assert(motor.isArmed());

        assert(policy.update(250) == BatterySafetyEvent::LOW_WARNING);
        assert(motor.isArmed());
        assert(policy.lowWarningActive());

        assert(policy.update(500) == BatterySafetyEvent::CRITICAL_DISARMED);
        assert(actions.disarms == 1);
        assert(policy.criticalLatched());
        assert(!policy.servoActivityAllowed());
        assert(motor.state() == MotorSafetyState::FAULT);
        assert(motor.lastDisarmReason() == MotorDisarmReason::LOW_BATTERY);
        assert(!motor.isDriverEnabled());

        // 6.10 V is still CRITICAL because BatteryMonitor hysteresis requires 6.20 V.
        assert(policy.update(750) == BatterySafetyEvent::NONE);
        assert(policy.criticalLatched());
        assert(motor.state() == MotorSafetyState::FAULT);
        assert(!motor.arm());

        // 6.21 V exits CRITICAL to LOW. Recovery clears only FAULT -> SAFE.
        assert(policy.update(1000) == BatterySafetyEvent::RECOVERED_SAFE);
        assert(actions.recoveries == 1);
        assert(!policy.criticalLatched());
        assert(policy.servoActivityAllowed());
        assert(motor.state() == MotorSafetyState::SAFE);
        assert(!motor.isArmed());
        assert(!motor.isDriverEnabled());

        // A fresh START-equivalent arm is still required after recovery.
        assert(motor.arm());
        assert(motor.isArmed());

        assert(policy.update(1250) == BatterySafetyEvent::LOW_WARNING);
    }

    {
        // INVALID before any critical event must not invent a LOW_BATTERY fault.
        FakeAdc adc{0};
        BatteryMonitor monitor(adc, cfg());
        FakeGate gate;
        MotorSafetyController motor(gate, true);
        motor.begin();
        assert(motor.arm());
        Actions actions(motor);
        BatterySafetyPolicy policy(monitor, actions);

        assert(policy.update(0) == BatterySafetyEvent::INVALID_READING);
        assert(actions.disarms == 0);
        assert(!policy.criticalLatched());
        assert(policy.servoActivityAllowed());
        assert(motor.isArmed());
    }

    {
        // INVALID after CRITICAL must not clear the safety latch.
        FakeAdc adc{590, 0};
        BatteryMonitor monitor(adc, cfg());
        FakeGate gate;
        MotorSafetyController motor(gate, true);
        motor.begin();
        assert(motor.arm());
        Actions actions(motor);
        BatterySafetyPolicy policy(monitor, actions);

        assert(policy.update(0) == BatterySafetyEvent::CRITICAL_DISARMED);
        assert(policy.update(250) == BatterySafetyEvent::INVALID_READING);
        assert(policy.criticalLatched());
        assert(!policy.servoActivityAllowed());
        assert(motor.state() == MotorSafetyState::FAULT);
    }

    {
        // Recovery API must be reason-specific; another fault cannot be
        // cleared by battery recovery.
        FakeGate gate;
        MotorSafetyController motor(gate, true);
        motor.begin();
        assert(motor.arm());
        motor.disarm(MotorDisarmReason::FATAL_PLATFORM_FAULT);
        assert(!motor.recoverFaultToSafe(MotorDisarmReason::LOW_BATTERY));
        assert(motor.state() == MotorSafetyState::FAULT);
    }

    return 0;
}
"""

def test_real_battery_safety_cpp() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "battery_safety_test.cpp"
        exe = td / "battery_safety_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HEALTH), "-I", str(HAL),
            str(src),
            str(HEALTH / "BatteryMonitor.cpp"),
            str(HEALTH / "BatterySafetyPolicy.cpp"),
            str(HAL / "MotorSafetyController.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_runtime_order_and_servo_policy() -> None:
    main = MAIN.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    platform = (HEALTH / "BatterySafetyPlatform.cpp").read_text(encoding="utf-8")

    battery_pos = main.index("systemBatterySafetyPolicy().update(millis())")
    start_pos = main.index("systemStartArm().update(millis())")
    assert battery_pos < start_pos, "battery CRITICAL must be evaluated before START arm"

    servo_start = api.index("void SetServo(int port, int angle)")
    servo_end = api.index("void Set3CLed", servo_start)
    servo = api[servo_start:servo_end]
    assert "systemBatterySafetyPolicy().servoActivityAllowed()" in servo
    assert "Blocked by CRITICAL battery safety policy" in servo

    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::LOW_BATTERY)" in platform
    assert "recoverFaultToSafe(MotorDisarmReason::LOW_BATTERY)" in platform


def test_uncalibrated_production_does_not_fake_critical() -> None:
    monitor_h = (HEALTH / "BatteryMonitor.h").read_text(encoding="utf-8")
    policy = (HEALTH / "BatterySafetyPolicy.cpp").read_text(encoding="utf-8")
    assert "calibrationValid = false" in monitor_h
    assert "_monitor.sample()" in policy
    assert "INVALID_READING" in policy
    assert "disarmForCriticalBattery" not in policy.split("if (!_monitor.sample())", 1)[1].split("if (_lastState == BatteryState::CRITICAL)", 1)[0]


def main() -> int:
    test_real_battery_safety_cpp()
    print("PASS: real BatterySafetyPolicy critical/low/recovery/invalid behavior")
    test_runtime_order_and_servo_policy()
    print("PASS: CRITICAL check precedes START and blocks new servo activity")
    test_uncalibrated_production_does_not_fake_critical()
    print("PASS: uncalibrated INVALID battery does not invent CRITICAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
