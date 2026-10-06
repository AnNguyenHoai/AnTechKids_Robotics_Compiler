from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
MAIN = ROOT / "robot-platform/main/main.ino"
API_H = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.h"
VM_H = ROOT / "robot-platform/main/src/Services/VM/VM.h"
PROFILE = HAL / "BoardProfile.h"

HARNESS = r"""
#include <cassert>
#include "StartArmController.h"

struct FakeInput : IStartArmInput {
    bool began = false;
    bool pressed = false;

    void begin() override { began = true; }
    bool isPressed() override { return pressed; }
};

struct FakeGate : IMotorSafetyGate {
    bool enabled = true;
    void beginSafe() override { enabled = false; }
    void setDriverEnabled(bool value) override { enabled = value; }
};

static void settle(StartArmController& start, uint32_t changeAt) {
    start.update(changeAt);
    start.update(changeAt + StartArmController::DEBOUNCE_MS);
}

int main() {
    {
        FakeInput input;
        FakeGate gate;
        MotorSafetyController safety(gate, true);
        safety.begin();

        StartArmController start(input, safety);
        start.begin(0);
        assert(input.began);
        assert(!start.isPressed());
        assert(!start.armedByStartThisBoot());

        // Student/motion code can run before readiness, but START cannot arm.
        input.pressed = true;
        settle(start, 10);
        assert(!safety.isArmed());

        input.pressed = false;
        settle(start, 50);
        assert(!safety.isArmed());

        start.onSystemReady(100);
        assert(start.isReadyForPress());

        input.pressed = true;
        assert(!start.update(110)); // raw edge
        assert(!start.update(139)); // not yet debounced
        assert(start.update(140));  // stable press arms
        assert(safety.isArmed());
        assert(start.isPressed());
        assert(start.armedByStartThisBoot());

        // Holding START cannot repeatedly arm.
        assert(!start.update(200));

        safety.disarm(MotorDisarmReason::EXPLICIT_SAFETY_STOP);
        assert(!safety.isArmed());
        assert(!start.update(210)); // still held; no re-arm

        input.pressed = false;
        settle(start, 220);
        input.pressed = true;
        assert(!start.update(260));
        assert(start.update(290)); // new release->press edge may re-arm
        assert(safety.isArmed());
    }

    {
        // Held during boot/readiness must never auto-arm.
        FakeInput input;
        input.pressed = true;
        FakeGate gate;
        MotorSafetyController safety(gate, true);
        safety.begin();

        StartArmController start(input, safety);
        start.begin(0);
        start.onSystemReady(100);
        assert(start.isPressed());
        assert(!start.isReadyForPress());
        assert(!start.update(1000));
        assert(!safety.isArmed());

        input.pressed = false;
        assert(!start.update(1010));
        assert(!start.update(1039));
        assert(!start.update(1040)); // release accepted, no arm
        assert(start.isReadyForPress());

        input.pressed = true;
        assert(!start.update(1100));
        assert(start.update(1130));
        assert(safety.isArmed());
    }

    {
        // Press begins during setup but was not present at begin(): readiness
        // re-sample still forces release before any ARM.
        FakeInput input;
        FakeGate gate;
        MotorSafetyController safety(gate, true);
        safety.begin();

        StartArmController start(input, safety);
        start.begin(0);
        input.pressed = true;
        start.onSystemReady(500);
        assert(!start.isReadyForPress());
        assert(!start.update(1000));
        assert(!safety.isArmed());
    }

    {
        // MOTOR feature OFF cannot arm even from the approved START path.
        FakeInput input;
        FakeGate gate;
        MotorSafetyController safety(gate, false);
        safety.begin();
        StartArmController start(input, safety);
        start.begin(0);
        start.onSystemReady(10);
        input.pressed = true;
        assert(!start.update(20));
        assert(!start.update(50));
        assert(!safety.isArmed());
        assert(!gate.enabled);
    }

    return 0;
}
"""

def test_real_start_arm_cpp() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "start_arm_test.cpp"
        exe = td / "start_arm_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HAL),
            str(src),
            str(HAL / "MotorSafetyController.cpp"),
            str(HAL / "StartArmController.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_gpio33_active_low_and_runtime_integration() -> None:
    profile = PROFILE.read_text(encoding="utf-8")
    gpio = (HAL / "StartArmGpioInput.cpp").read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")

    assert "START_ARM = 33" in profile
    assert "BoardProfile::Pins::START_ARM" in gpio
    assert "INPUT_PULLUP_MODE" in gpio
    assert "PinState::LOW_STATE" in gpio

    assert "systemStartArm().begin(millis())" in main
    assert "systemStartArm().onSystemReady(millis())" in main
    assert "systemStartArm().update(millis())" in main

    ready_pos = main.index("systemStartArm().onSystemReady(millis())")
    vm_loop_pos = main.index("void loop()")
    assert ready_pos < vm_loop_pos

    ota_pos = main.index("if (RobotNetworkService::isUpdateInProgress())")
    update_pos = main.index("systemStartArm().update(millis())")
    assert ota_pos < update_pos


def test_student_surfaces_have_no_arm_api() -> None:
    api_h = API_H.read_text(encoding="utf-8")
    vm_h = VM_H.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    start_cpp = (HAL / "StartArmController.cpp").read_text(encoding="utf-8")

    assert "MotorSafety" not in api_h
    assert " arm(" not in api_h.lower()
    assert "MotorSafety" not in vm_h
    assert ".arm()" not in main
    assert "_motorSafety.arm()" in start_cpp


def test_health_ready_read_only_surface() -> None:
    header = (HAL / "StartArmController.h").read_text(encoding="utf-8")
    assert "bool isPressed() const" in header
    assert "bool isReadyForPress() const" in header
    assert "bool armedByStartThisBoot() const" in header


def main() -> int:
    test_real_start_arm_cpp()
    print("PASS: real StartArmController debounce/readiness/held-boot behavior")
    test_gpio33_active_low_and_runtime_integration()
    print("PASS: GPIO33 active-low START integrated after readiness and outside OTA")
    test_student_surfaces_have_no_arm_api()
    print("PASS: student RobotAPI/VM surfaces cannot arm MotorSafety directly")
    test_health_ready_read_only_surface()
    print("PASS: START state exposes read-only surface for future RobotHealth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
