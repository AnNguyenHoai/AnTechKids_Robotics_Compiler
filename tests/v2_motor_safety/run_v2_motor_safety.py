from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
API = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
PROFILE = HAL / "BoardProfile.h"

HARNESS = r"""
#include <cassert>
#include "MotorSafetyController.h"

struct FakeGate : IMotorSafetyGate {
    bool began = false;
    bool enabled = true;
    int enableWrites = 0;

    void beginSafe() override {
        began = true;
        enabled = false;
    }

    void setDriverEnabled(bool value) override {
        enabled = value;
        enableWrites++;
    }
};

int main() {
    {
        FakeGate gate;
        MotorSafetyController safety(gate, true);

        assert(safety.state() == MotorSafetyState::BOOT);
        assert(!safety.isArmed());
        assert(!safety.isDriverEnabled());

        safety.begin();
        assert(gate.began);
        assert(!gate.enabled);
        assert(safety.state() == MotorSafetyState::SAFE);
        assert(!safety.allowPhysicalOutput(20, 20));
        assert(safety.allowPhysicalOutput(0, 0));

        assert(safety.arm());
        assert(gate.enabled);
        assert(safety.isArmed());
        assert(safety.state() == MotorSafetyState::ARMED);

        assert(safety.allowPhysicalOutput(40, 40));
        assert(safety.state() == MotorSafetyState::RUNNING);
        assert(safety.allowPhysicalOutput(0, 0));
        assert(safety.state() == MotorSafetyState::ARMED);

        safety.disarm(MotorDisarmReason::OTA);
        assert(!gate.enabled);
        assert(!safety.isArmed());
        assert(safety.state() == MotorSafetyState::SAFE);
        assert(safety.lastDisarmReason() == MotorDisarmReason::OTA);
        assert(!safety.allowPhysicalOutput(50, -50));
    }

    {
        FakeGate gate;
        MotorSafetyController safety(gate, true);
        safety.begin();
        assert(safety.arm());
        safety.disarm(MotorDisarmReason::LOW_BATTERY);
        assert(safety.state() == MotorSafetyState::FAULT);
        assert(!safety.isDriverEnabled());
        assert(!safety.arm()); // fault requires external recovery policy/reset
        assert(!gate.enabled);
    }

    {
        // HardwareConfig MOTOR OFF must never enable STBY.
        FakeGate gate;
        MotorSafetyController safety(gate, false);
        safety.begin();
        assert(!safety.arm());
        assert(!gate.enabled);
        assert(!safety.allowPhysicalOutput(100, 100));
    }

    return 0;
}
"""

def test_real_motor_safety_cpp() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "motor_safety_test.cpp"
        exe = td / "motor_safety_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HAL),
            str(src), str(HAL / "MotorSafetyController.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_physical_gate_and_lowest_output_boundary() -> None:
    profile = PROFILE.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    gate = (HAL / "MotorSafetyGpioGate.cpp").read_text(encoding="utf-8")
    platform = (HAL / "MotorSafetyPlatform.cpp").read_text(encoding="utf-8")

    assert "MOTOR_SAFE_EN = 4" in profile
    assert "BoardProfile::Pins::MOTOR_SAFE_EN" in gate
    assert "PinState::LOW_STATE" in gate
    assert "PinState::HIGH_STATE" in gate
    assert "ROBOT_FEATURE_MOTOR != 0" in platform

    raw_start = api.index("static void _setMotorsRaw")
    raw_end = api.index("// H23-A ownership boundary", raw_start)
    raw = api[raw_start:raw_end]
    gate_pos = raw.index("systemMotorSafety().allowPhysicalOutput")
    pwm_pos = raw.index("ledcWrite(MOTOR_L_IN1_PIN, leftPWM)")
    assert gate_pos < pwm_pos
    assert "ledcWrite(MOTOR_L_IN1_PIN, 0)" in raw
    assert "ledcWrite(MOTOR_R_IN4_PIN, 0)" in raw

    init_start = api.index("void Initialize()")
    init_end = api.index("loadMotionConfigFromStorage()", init_start)
    init = api[init_start:init_end]
    assert "systemMotorSafety().begin();" in init
    assert init.index("systemMotorSafety().begin();") < api[init_start:].index("pinMode(MOTOR_L_IN1_PIN", 0) if "pinMode(MOTOR_L_IN1_PIN" in api[init_start:] else True


def test_no_public_motion_bypass_of_raw_path() -> None:
    api = API.read_text(encoding="utf-8")
    # All physical motor PWM writes must remain inside _setMotorsRaw.
    occurrences = [i for i in range(len(api)) if api.startswith("ledcWrite(MOTOR_", i)]
    raw_start = api.index("static void _setMotorsRaw")
    raw_end = api.index("// H23-A ownership boundary", raw_start)
    assert occurrences
    assert all(raw_start <= i < raw_end for i in occurrences)


def main() -> int:
    test_real_motor_safety_cpp()
    print("PASS: real MotorSafetyController state/gate behavior with fake physical gate")
    test_physical_gate_and_lowest_output_boundary()
    print("PASS: GPIO4 STBY defaults LOW and lowest PWM path enforces safety")
    test_no_public_motion_bypass_of_raw_path()
    print("PASS: no physical motor PWM write exists outside centralized raw path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
