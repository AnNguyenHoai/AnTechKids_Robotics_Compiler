from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
API_CPP = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
LEDC = ROOT / "robot-platform/main/src/Compatibility/LEDCCompat.h"
HANDLER = ROOT / "robot-compiler/compiler/handlers/servo_handler.py"
VM = ROOT / "robot-platform/main/src/Services/VM/VM.cpp"

sys.path.insert(0, str(ROOT / "robot-compiler"))
from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode

HARNESS = r"""
#include <cassert>
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
    assert(ServoHAL::clampAngle(-10) == 0);
    assert(ServoHAL::clampAngle(0) == 0);
    assert(ServoHAL::clampAngle(90) == 90);
    assert(ServoHAL::clampAngle(180) == 180);
    assert(ServoHAL::clampAngle(250) == 180);

    uint8_t pin = 0;
    assert(ServoHAL::pinForPort(1, pin) && pin == 16);
    assert(ServoHAL::pinForPort(2, pin) && pin == 17);
    assert(!ServoHAL::pinForPort(0, pin));
    assert(!ServoHAL::pinForPort(3, pin));

    const uint32_t d0 = ServoHAL::angleToDuty(0);
    const uint32_t d90 = ServoHAL::angleToDuty(90);
    const uint32_t d180 = ServoHAL::angleToDuty(180);
    assert(d0 < d90 && d90 < d180);
    assert(ServoHAL::angleToDuty(-50) == d0);
    assert(ServoHAL::angleToDuty(250) == d180);

    FakePwm pwm;
    ServoHAL servo(pwm);

    assert(servo.setAngle(1, 90));
    assert(pwm.attaches.size() == 1);
    assert(pwm.attaches[0].pin == 16);
    assert(pwm.writes.size() == 1);
    assert(pwm.writes[0].pin == 16);
    assert(pwm.writes[0].value == d90);

    // Lazy attach: repeated commands on the same port do not reattach PWM.
    assert(servo.setAngle(1, 180));
    assert(pwm.attaches.size() == 1);
    assert(pwm.writes.back().value == d180);

    assert(servo.setAngle(2, 0));
    assert(pwm.attaches.size() == 2);
    assert(pwm.attaches[1].pin == 17);
    assert(pwm.writes.back().pin == 17);

    const size_t attachCount = pwm.attaches.size();
    const size_t writeCount = pwm.writes.size();
    assert(!servo.setAngle(3, 90));
    assert(servo.lastError() == ServoError::INVALID_PORT);
    assert(pwm.attaches.size() == attachCount);
    assert(pwm.writes.size() == writeCount);

    FakePwm failAttach;
    failAttach.attachOk = false;
    ServoHAL servoFailAttach(failAttach);
    assert(!servoFailAttach.setAngle(1, 90));
    assert(servoFailAttach.lastError() == ServoError::PWM_ERROR);

    FakePwm failWrite;
    failWrite.writeOk = false;
    ServoHAL servoFailWrite(failWrite);
    assert(!servoFailWrite.setAngle(2, 90));
    assert(servoFailWrite.lastError() == ServoError::PWM_ERROR);

    return 0;
}
"""

def test_real_cpp_servo_hal() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "servo_hal_test.cpp"
        exe = td / "servo_hal_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HAL),
            str(src), str(HAL / "ServoHAL.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_platform_contract() -> None:
    api = API_CPP.read_text(encoding="utf-8")
    ledc = LEDC.read_text(encoding="utf-8")
    assert "#if !ROBOT_FEATURE_SERVO" in api
    start = api.index("void SetServo(int port, int angle)")
    end = api.index("void Set3CLed", start)
    body = api[start:end]
    assert "[DUMMY][SetServo]" not in body
    assert "g_servoHAL.setAngle(port, angle)" in body
    assert "ServoHAL::clampAngle(angle)" in body
    assert "MotorSafety" not in body
    assert "case 16: return 4;" in ledc
    assert "case 17: return 5;" in ledc


def test_compiler_vm_transport() -> None:
    handler = HANDLER.read_text(encoding="utf-8")
    assert "Opcode.SetServo.value" in handler
    assert "intentionally emits no runtime bytecode" not in handler.split("def set_servo", 1)[1].split("def set_seering_engine", 1)[0]

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "servo.py"
        path.write_text("set_servo(2, 190)\n", encoding="utf-8")
        program = RobotCompiler(target="esp32").compile(path)

    servo_ops = [ins for ins in program.instructions if ins.opcode == Opcode.SetServo.value]
    assert len(servo_ops) == 1, f"Expected one SetServo opcode, got {len(servo_ops)}"

    vm = VM.read_text(encoding="utf-8")
    assert "case Opcode::SetServo:" in vm
    assert "RobotAPI::SetServo" in vm


def test_no_motor_safety_or_motor_pin_coupling() -> None:
    combined = (
        (HAL / "ServoHAL.h").read_text(encoding="utf-8") +
        (HAL / "ServoHAL.cpp").read_text(encoding="utf-8") +
        (HAL / "ServoLEDCTransport.cpp").read_text(encoding="utf-8")
    )
    for forbidden in ("MotorSafety", "MOTOR_SAFE_EN", "MOTOR_L_IN", "MOTOR_R_IN"):
        assert forbidden not in combined, forbidden


def main() -> int:
    test_real_cpp_servo_hal()
    print("PASS: real ServoHAL C++ logic with mock PWM transport")
    test_platform_contract()
    print("PASS: RobotAPI feature guard and ESP32 LEDC mapping")
    test_compiler_vm_transport()
    print("PASS: compiler -> SetServo opcode -> VM -> RobotAPI transport")
    test_no_motor_safety_or_motor_pin_coupling()
    print("PASS: Servo HAL is independent from motor safety/output wiring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
