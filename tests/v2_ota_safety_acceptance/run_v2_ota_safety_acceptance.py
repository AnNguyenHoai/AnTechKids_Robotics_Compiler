from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
NETWORK = ROOT / "robot-platform/main/src/Communication/RobotNetworkService.cpp"
API = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
MAIN = ROOT / "robot-platform/main/main.ino"

HARNESS = r"""
#include <cassert>
#include "MotorSafetyController.h"
#include "StartArmController.h"

struct FakeGate : IMotorSafetyGate {
    bool enabled = true;
    void beginSafe() override { enabled = false; }
    void setDriverEnabled(bool value) override { enabled = value; }
};

struct FakeStart : IStartArmInput {
    bool pressed = false;
    void begin() override {}
    bool isPressed() override { return pressed; }
};

static void settle(StartArmController& start, FakeStart& input, bool pressed, uint32_t at) {
    input.pressed = pressed;
    assert(!start.update(at));
    start.update(at + StartArmController::DEBOUNCE_MS);
}

int main() {
    FakeGate gate;
    MotorSafetyController safety(gate, true);
    safety.begin();

    FakeStart input;
    StartArmController start(input, safety);
    start.begin(0);
    start.onSystemReady(100);

    // Fresh START arms the robot.
    input.pressed = true;
    assert(!start.update(110));
    assert(start.update(110 + StartArmController::DEBOUNCE_MS));
    assert(safety.isArmed());
    assert(safety.allowPhysicalOutput(70, 70));
    assert(safety.state() == MotorSafetyState::RUNNING);

    // OTA start is a hard transition to SAFE/STBY disabled.
    safety.disarm(MotorDisarmReason::OTA);
    assert(safety.state() == MotorSafetyState::SAFE);
    assert(!safety.isArmed());
    assert(!gate.enabled);
    assert(!safety.allowPhysicalOutput(70, 70));

    // A held START cannot undo OTA disarm.
    assert(!start.update(500));
    assert(!safety.isArmed());

    // Reboot creates a new controller and always starts SAFE.
    MotorSafetyController rebooted(gate, true);
    rebooted.begin();
    assert(rebooted.state() == MotorSafetyState::SAFE);
    assert(!rebooted.isArmed());
    assert(!gate.enabled);
    assert(!rebooted.allowPhysicalOutput(70, 70));

    // New boot requires a fresh START release -> press sequence.
    FakeStart rebootInput;
    rebootInput.pressed = true;
    StartArmController rebootStart(rebootInput, rebooted);
    rebootStart.begin(0);
    rebootStart.onSystemReady(100);
    assert(!rebootStart.update(1000));
    assert(!rebooted.isArmed());

    settle(rebootStart, rebootInput, false, 1100);
    assert(rebootStart.isReadyForPress());
    rebootInput.pressed = true;
    assert(!rebootStart.update(1200));
    assert(rebootStart.update(1200 + StartArmController::DEBOUNCE_MS));
    assert(rebooted.isArmed());
    return 0;
}
"""

def section(text: str, start: str, end: str) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b]


def test_real_ota_safety_state_machine() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "ota_safety.cpp"
        exe = td / "ota_safety"
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


def test_ota_start_disarms_before_update_work() -> None:
    network = NETWORK.read_text(encoding="utf-8")

    arduino = section(network, "void onOtaStart()", "void onOtaEnd()")
    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::OTA)" in arduino
    assert arduino.index("RobotMotorSafetyInternal::disarm") < arduino.index("setUpdateInProgress(true)")

    http = section(network, "void handleHttpOtaUpload()", "void handleHttpOtaFinish()")
    assert "UPLOAD_FILE_START" in http
    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::OTA)" in http
    assert http.index("RobotMotorSafetyInternal::disarm") < http.index("Update.begin(")


def test_disarm_clears_pwm_before_stby_and_update_pauses_student_code() -> None:
    api = API.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")

    disarm = section(api, "void disarm(MotorDisarmReason reason)", "} // namespace RobotMotorSafetyInternal")
    assert disarm.index("RobotAPI::_stopMotion") < disarm.index("systemMotorSafety().disarm(reason)")

    ota_guard = section(
        main,
        "if (RobotNetworkService::isUpdateInProgress())",
        "// V2-HLT-002: evaluate battery safety",
    )
    assert "RobotAPI::Stop();" in ota_guard
    assert "return;" in ota_guard
    assert "vm.Step()" not in ota_guard
    assert "scheduler.update()" not in ota_guard


def test_reboot_and_failure_paths_never_auto_arm() -> None:
    network = NETWORK.read_text(encoding="utf-8")
    finish = section(network, "void handleHttpOtaFinish()", "void registerHttpHandlers()")
    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::REBOOT)" in finish
    assert finish.index("RobotMotorSafetyInternal::disarm") < finish.index("ESP.restart()")

    # OTA failure/abort may clear update state, but must never arm.
    for start, end in (
        ("void onOtaError", "void handleHttpOtaUpload"),
        ("void handleHttpOtaUpload", "void handleHttpOtaFinish"),
        ("void handleHttpOtaFinish", "void registerHttpHandlers"),
    ):
        body = section(network, start, end)
        assert ".arm()" not in body
        assert "systemMotorSafety().arm" not in body


def test_boot_order_forces_safe_before_motor_pwm_and_requires_start() -> None:
    api = API.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")

    init = section(api, "void Initialize()", "} // namespace RobotAPI")
    safe = init.index("systemMotorSafety().begin()")
    pwm = init.index("ledcAttach(MOTOR_L_IN1_PIN")
    assert safe < pwm

    assert "systemStartArm().onSystemReady(millis())" in main
    assert "systemStartArm().update(millis())" in main
    assert "systemMotorSafety().arm()" not in main


def main() -> int:
    test_real_ota_safety_state_machine()
    print("PASS: ARMED -> OTA -> SAFE -> reboot SAFE -> fresh START state machine")
    test_ota_start_disarms_before_update_work()
    print("PASS: ArduinoOTA and HTTP OTA disarm before firmware update work")
    test_disarm_clears_pwm_before_stby_and_update_pauses_student_code()
    print("PASS: OTA clears motor output before STBY and pauses student execution")
    test_reboot_and_failure_paths_never_auto_arm()
    print("PASS: OTA reboot/failure paths never auto-arm")
    test_boot_order_forces_safe_before_motor_pwm_and_requires_start()
    print("PASS: reboot initializes MotorSafety SAFE before PWM and requires START")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
