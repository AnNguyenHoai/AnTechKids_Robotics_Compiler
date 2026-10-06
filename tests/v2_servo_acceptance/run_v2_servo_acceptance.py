from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
ROBOT = ROOT / "robot-platform/main/src/Services/Robot"
API_CPP = ROBOT / "RobotAPI.cpp"
API_H = ROBOT / "RobotAPI.h"
VM = ROOT / "robot-platform/main/src/Services/VM/VM.cpp"
HANDLER = ROOT / "robot-compiler/compiler/handlers/servo_handler.py"
CONFIG = ROOT / "robot-platform/main/include/generated/generated_device_config.h"

sys.path.insert(0, str(ROOT / "robot-compiler"))
from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode

HARNESS = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "ServoHAL.h"

struct Call {
    uint8_t pin;
    uint32_t value;
};

struct FakePwm : IServoPwmTransport {
    bool attachOk = true;
    bool writeOk = true;
    std::vector<Call> attaches;
    std::vector<Call> writes;

    bool attach(uint8_t pin, uint32_t frequencyHz, uint8_t resolutionBits) override {
        attaches.push_back({pin, frequencyHz * 100u + resolutionBits});
        return attachOk;
    }

    bool write(uint8_t pin, uint32_t duty) override {
        writes.push_back({pin, duty});
        return writeOk;
    }
};

int main() {
    // Required endpoint and clamp contract.
    assert(ServoHAL::clampAngle(-999) == 0);
    assert(ServoHAL::clampAngle(0) == 0);
    assert(ServoHAL::clampAngle(90) == 90);
    assert(ServoHAL::clampAngle(180) == 180);
    assert(ServoHAL::clampAngle(999) == 180);

    uint8_t pin = 0;
    assert(ServoHAL::pinForPort(1, pin) && pin == 16);
    assert(ServoHAL::pinForPort(2, pin) && pin == 17);
    assert(!ServoHAL::pinForPort(0, pin));
    assert(!ServoHAL::pinForPort(3, pin));

    const uint32_t d0 = ServoHAL::angleToDuty(0);
    const uint32_t d90 = ServoHAL::angleToDuty(90);
    const uint32_t d180 = ServoHAL::angleToDuty(180);
    assert(d0 < d90 && d90 < d180);
    assert(ServoHAL::angleToDuty(-1) == d0);
    assert(ServoHAL::angleToDuty(181) == d180);

    FakePwm pwm;
    ServoHAL servo(pwm);

    // Servo1: 0 / 90 / 180.
    assert(servo.setAngle(1, 0));
    assert(pwm.attaches.size() == 1);
    assert(pwm.attaches.back().pin == 16);
    assert(pwm.writes.back().value == d0);

    assert(servo.setAngle(1, 90));
    assert(pwm.attaches.size() == 1); // lazy attach
    assert(pwm.writes.back().value == d90);

    assert(servo.setAngle(1, 180));
    assert(pwm.writes.back().value == d180);

    // Servo2: 0 / 90 / 180 and independent attach.
    assert(servo.setAngle(2, 0));
    assert(pwm.attaches.size() == 2);
    assert(pwm.attaches.back().pin == 17);
    assert(pwm.writes.back().value == d0);

    assert(servo.setAngle(2, 90));
    assert(pwm.writes.back().value == d90);
    assert(servo.setAngle(2, 180));
    assert(pwm.writes.back().value == d180);

    // Out-of-range values are clamped before duty generation.
    assert(servo.setAngle(1, -20));
    assert(pwm.writes.back().value == d0);
    assert(servo.setAngle(2, 250));
    assert(pwm.writes.back().value == d180);

    // Invalid port never attaches or writes.
    const size_t attachCount = pwm.attaches.size();
    const size_t writeCount = pwm.writes.size();
    assert(!servo.setAngle(0, 90));
    assert(servo.lastError() == ServoError::INVALID_PORT);
    assert(pwm.attaches.size() == attachCount);
    assert(pwm.writes.size() == writeCount);

    // PWM transport failures are reported and never become a false success.
    FakePwm attachFail;
    attachFail.attachOk = false;
    ServoHAL servoAttachFail(attachFail);
    assert(!servoAttachFail.setAngle(1, 90));
    assert(servoAttachFail.lastError() == ServoError::PWM_ERROR);
    assert(attachFail.writes.empty());

    FakePwm writeFail;
    writeFail.writeOk = false;
    ServoHAL servoWriteFail(writeFail);
    assert(!servoWriteFail.setAngle(2, 90));
    assert(servoWriteFail.lastError() == ServoError::PWM_ERROR);

    return 0;
}
"""


def test_integrated_real_servo_hal_cpp() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "servo_acceptance.cpp"
        exe = td / "servo_acceptance"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HAL),
            str(src), str(HAL / "ServoHAL.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_fixed_board_mapping_and_pwm_contract() -> None:
    header = (HAL / "ServoHAL.h").read_text(encoding="utf-8")
    impl = (HAL / "ServoHAL.cpp").read_text(encoding="utf-8")
    board = (HAL / "BoardProfile.h").read_text(encoding="utf-8")

    assert "SERVO1 = 16" in board
    assert "SERVO2 = 17" in board
    assert "BoardProfile::Pins::SERVO1" in impl
    assert "BoardProfile::Pins::SERVO2" in impl

    assert "PWM_FREQUENCY_HZ = 50" in header
    assert "PWM_RESOLUTION_BITS = 16" in header
    assert "MIN_PULSE_US = 500" in header
    assert "MAX_PULSE_US = 2500" in header
    assert "PERIOD_US = 20000" in header


def test_feature_off_and_critical_battery_are_non_drive_paths() -> None:
    api = API_CPP.read_text(encoding="utf-8")
    start = api.index("void SetServo(int port, int angle)")
    end = api.index("void Set3CLed", start)
    body = api[start:end]

    assert "#if !ROBOT_FEATURE_SERVO" in body
    off_start = body.index("#if !ROBOT_FEATURE_SERVO")
    off_end = body.index("#else", off_start)
    off = body[off_start:off_end]
    assert "g_servoHAL" not in off
    assert "setAngle" not in off

    assert "systemBatterySafetyPolicy().servoActivityAllowed()" in body
    battery_gate = body.index("systemBatterySafetyPolicy().servoActivityAllowed()")
    drive = body.index("g_servoHAL.setAngle(port, angle)")
    assert battery_gate < drive
    assert "Blocked by CRITICAL battery safety policy" in body


def test_public_api_and_compiler_vm_transport() -> None:
    header = API_H.read_text(encoding="utf-8")
    handler = HANDLER.read_text(encoding="utf-8")
    vm = VM.read_text(encoding="utf-8")

    assert "void SetServo(int port, int angle);" in header
    assert "Opcode.SetServo.value" in handler
    assert "case Opcode::SetServo:" in vm
    assert "RobotAPI::SetServo" in vm

    with tempfile.TemporaryDirectory() as td:
        program_file = Path(td) / "servo_acceptance.py"
        program_file.write_text(
            "set_servo(1, 0)\nset_servo(2, 90)\nset_servo(1, 180)\n",
            encoding="utf-8",
        )
        program = RobotCompiler(target="esp32").compile(program_file)

    ops = [ins for ins in program.instructions if ins.opcode == Opcode.SetServo.value]
    assert len(ops) == 3


def test_servo_has_no_motor_pin_or_stby_ownership() -> None:
    combined = "\n".join(
        (HAL / name).read_text(encoding="utf-8")
        for name in ("ServoHAL.h", "ServoHAL.cpp", "ServoLEDCTransport.cpp")
    )
    for forbidden in (
        "MOTOR_SAFE_EN",
        "MOTOR_L_IN1",
        "MOTOR_L_IN2",
        "MOTOR_R_IN3",
        "MOTOR_R_IN4",
        "systemMotorSafety",
    ):
        assert forbidden not in combined, forbidden


def main() -> int:
    test_integrated_real_servo_hal_cpp()
    print("PASS: integrated real ServoHAL covers Servo1/Servo2 endpoints, clamp, invalid port and PWM failures")
    test_fixed_board_mapping_and_pwm_contract()
    print("PASS: Servo ports and current PWM contract are fixed by BoardProfile/ServoHAL")
    test_feature_off_and_critical_battery_are_non_drive_paths()
    print("PASS: feature OFF and CRITICAL battery paths cannot submit servo PWM")
    test_public_api_and_compiler_vm_transport()
    print("PASS: public API and compiler -> VM -> RobotAPI SetServo transport remain compatible")
    test_servo_has_no_motor_pin_or_stby_ownership()
    print("PASS: Servo HAL does not own motor pins or MotorSafety STBY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
