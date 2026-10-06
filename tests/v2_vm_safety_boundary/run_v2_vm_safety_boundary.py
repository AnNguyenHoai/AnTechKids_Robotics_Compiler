from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
VM = ROOT / "robot-platform/main/src/Services/VM/VM.cpp"
API_CPP = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
API_H = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.h"
START = HAL / "StartArmController.cpp"
MAIN = ROOT / "robot-platform/main/main.ino"

HARNESS = r"""
#include <cassert>
#include "MotorSafetyController.h"

struct FakeGate : IMotorSafetyGate {
    bool enabled = true;
    void beginSafe() override { enabled = false; }
    void setDriverEnabled(bool value) override { enabled = value; }
};

int main() {
    FakeGate gate;
    MotorSafetyController safety(gate, true);

    safety.begin();
    assert(safety.state() == MotorSafetyState::SAFE);
    assert(!safety.isArmed());
    assert(!gate.enabled);

    // SAFE does not prohibit software execution; it prohibits physical motion.
    assert(safety.allowPhysicalOutput(0, 0));
    assert(!safety.allowPhysicalOutput(40, 40));
    assert(!gate.enabled);

    assert(safety.arm());
    assert(safety.allowPhysicalOutput(40, -40));
    assert(safety.state() == MotorSafetyState::RUNNING);
    assert(gate.enabled);

    safety.disarm(MotorDisarmReason::EXPLICIT_SAFETY_STOP);
    assert(safety.state() == MotorSafetyState::SAFE);
    assert(!safety.allowPhysicalOutput(40, 40));
    assert(!gate.enabled);
    return 0;
}
"""

def function_slice(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def test_real_motor_gate_blocks_nonzero_output_while_safe() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "vm_safety_boundary.cpp"
        exe = td / "vm_safety_boundary"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HAL),
            str(src),
            str(HAL / "MotorSafetyController.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_vm_execution_is_not_arm_gated() -> None:
    vm = VM.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")

    # VM owns program execution, not physical motor permission.
    for forbidden in (
        "MotorSafetyController",
        "RobotMotorSafetyInternal",
        "systemMotorSafety",
        ".arm()",
        ".disarm(",
    ):
        assert forbidden not in vm, forbidden

    # Logic and sensor instructions are dispatched normally with no ARM check.
    for opcode in (
        "Opcode::LoadConst",
        "Opcode::CompareEQ",
        "Opcode::Add",
        "Opcode::ReadUltrasonic",
        "Opcode::ReadLine",
    ):
        assert f"case {opcode}" in vm, opcode

    # Platform loop continues stepping VM while robot is ready; it does not
    # require MotorSafety ARMED state before executing student logic.
    assert "if (vm.IsRunning())" in main
    assert "vm.Step();" in main
    assert "systemMotorSafety().isArmed()" not in main


def test_vm_motion_stays_behind_robotapi_and_physical_gate() -> None:
    vm = VM.read_text(encoding="utf-8")
    api = API_CPP.read_text(encoding="utf-8")

    required_dispatch = {
        "Opcode::Forward": "RobotAPI::Forward",
        "Opcode::Backward": "RobotAPI::Backward",
        "Opcode::TurnLeft": "RobotAPI::TurnLeft",
        "Opcode::TurnRight": "RobotAPI::TurnRight",
        "Opcode::SetMotorSpeed": "RobotAPI::SetMotorSpeed",
        "Opcode::LineBasis": "RobotAPI::LineBasis",
        "Opcode::LineFollow": "RobotAPI::LineFollow",
    }
    for opcode, call in required_dispatch.items():
        start = vm.index(f"case {opcode}")
        end = vm.index("break;", start)
        assert call in vm[start:end], (opcode, call)

    raw = function_slice(api, "static void _setMotorsRaw", "// H23-A ownership boundary:")
    gate = raw.index("systemMotorSafety().allowPhysicalOutput")
    first_nonzero_path = raw.index("// ---- NORMAL PWM OUTPUT")
    assert gate < first_nonzero_path

    blocked = raw[:first_nonzero_path]
    for pin in (
        "MOTOR_L_IN1_PIN",
        "MOTOR_L_IN2_PIN",
        "MOTOR_R_IN3_PIN",
        "MOTOR_R_IN4_PIN",
    ):
        assert f"ledcWrite({pin}, 0)" in blocked


def test_student_surface_cannot_arm_or_disarm() -> None:
    api_h = API_H.read_text(encoding="utf-8")
    vm = VM.read_text(encoding="utf-8")
    start = START.read_text(encoding="utf-8")

    for forbidden in (
        "MotorSafetyController",
        "MotorDisarmReason",
        "RobotMotorSafetyInternal",
        "systemMotorSafety",
    ):
        assert forbidden not in api_h, forbidden

    assert ".arm()" not in vm
    assert ".disarm(" not in vm
    assert "_motorSafety.arm()" in start


def main() -> int:
    test_real_motor_gate_blocks_nonzero_output_while_safe()
    print("PASS: real MotorSafety gate blocks non-zero physical output while SAFE")
    test_vm_execution_is_not_arm_gated()
    print("PASS: VM logic/sensor execution remains independent from ARM state")
    test_vm_motion_stays_behind_robotapi_and_physical_gate()
    print("PASS: VM motion dispatch remains behind RobotAPI and the physical safety gate")
    test_student_surface_cannot_arm_or_disarm()
    print("PASS: student/VM surfaces cannot arm or disarm MotorSafety")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
