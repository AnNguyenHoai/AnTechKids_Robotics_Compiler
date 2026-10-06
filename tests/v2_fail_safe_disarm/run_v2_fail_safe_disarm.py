from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_CPP = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
API_H = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.h"
INTERNAL_H = ROOT / "robot-platform/main/src/Services/Robot/RobotMotorSafetyInternal.h"
NETWORK = ROOT / "robot-platform/main/src/Communication/RobotNetworkService.cpp"
SERIAL = ROOT / "robot-platform/main/src/Communication/SerialCommandHandler.cpp"
MAIN = ROOT / "robot-platform/main/main.ino"
CTRL = ROOT / "robot-platform/main/src/HardwareAbstraction/MotorSafetyController.cpp"
START = ROOT / "robot-platform/main/src/HardwareAbstraction/StartArmController.cpp"


def function_slice(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def test_system_disarm_clears_pwm_before_stby() -> None:
    api = API_CPP.read_text(encoding="utf-8")
    body = function_slice(
        api,
        "void disarm(MotorDisarmReason reason)",
        "} // namespace RobotMotorSafetyInternal",
    )
    stop_pos = body.index("RobotAPI::_stopMotion")
    disarm_pos = body.index("systemMotorSafety().disarm(reason)")
    assert stop_pos < disarm_pos, "PWM/motion state must clear before STBY disarm"


def test_ota_paths_disarm_and_arduino_callbacks_are_registered() -> None:
    network = NETWORK.read_text(encoding="utf-8")

    start = function_slice(network, "void onOtaStart()", "void onOtaEnd()")
    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::OTA)" in start

    http = function_slice(network, "void handleHttpOtaUpload()", "void handleHttpOtaFinish()")
    assert "UPLOAD_FILE_START" in http
    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::OTA)" in http
    assert "RobotAPI::Stop()" not in http

    finish = function_slice(network, "void handleHttpOtaFinish()", "void registerHttpHandlers()")
    assert "RobotMotorSafetyInternal::disarm(MotorDisarmReason::REBOOT)" in finish
    assert finish.index("RobotMotorSafetyInternal::disarm") < finish.index("ESP.restart()")

    for hook in (
        "ArduinoOTA.onStart(onOtaStart);",
        "ArduinoOTA.onEnd(onOtaEnd);",
        "ArduinoOTA.onProgress(onOtaProgress);",
        "ArduinoOTA.onError(onOtaError);",
    ):
        assert hook in network, hook

    # OTA errors/abort/failures never call arm(); once OTA start disarms,
    # failure leaves the robot SAFE until a fresh START press.
    assert ".arm()" not in network


def test_fatal_halts_disarm() -> None:
    main = MAIN.read_text(encoding="utf-8")
    assert 'Failed to load program. Motors disarmed; halted.' in main
    assert 'IMU calibration failure; motors disarmed' in main
    assert 'VM stopped with error code: %d; motors disarmed' in main
    assert main.count("MotorDisarmReason::FATAL_PLATFORM_FAULT") >= 3


def test_explicit_safety_stop_is_operator_only() -> None:
    serial = SERIAL.read_text(encoding="utf-8")
    api_h = API_H.read_text(encoding="utf-8")
    internal = INTERNAL_H.read_text(encoding="utf-8")

    assert 'input == "safety stop"' in serial
    assert "MotorDisarmReason::EXPLICIT_SAFETY_STOP" in serial
    assert "RobotMotorSafetyInternal" in internal

    # Normal student Stop remains a motion stop, not a safety disarm.
    assert "MotorDisarmReason" not in api_h
    assert "RobotMotorSafetyInternal" not in api_h


def test_fault_and_reset_policy_contract() -> None:
    ctrl = CTRL.read_text(encoding="utf-8")
    start = START.read_text(encoding="utf-8")

    for reason in (
        "LOW_BATTERY",
        "FATAL_PLATFORM_FAULT",
        "MOTOR_SAFETY_FAULT",
        "WATCHDOG",
    ):
        assert f"MotorDisarmReason::{reason}" in ctrl

    assert "_lastDisarmReason = MotorDisarmReason::RESET;" in ctrl
    assert "_state = MotorSafetyState::SAFE;" in ctrl

    # After disarm, only START controller owns the re-arm call.
    assert "_motorSafety.arm()" in start


def main() -> int:
    test_system_disarm_clears_pwm_before_stby()
    print("PASS: fail-safe boundary clears PWM before disabling STBY")
    test_ota_paths_disarm_and_arduino_callbacks_are_registered()
    print("PASS: ArduinoOTA/HTTP OTA start, failure persistence and reboot safety")
    test_fatal_halts_disarm()
    print("PASS: fatal platform halt paths disarm before blocking")
    test_explicit_safety_stop_is_operator_only()
    print("PASS: explicit safety stop exists without changing student Stop semantics")
    test_fault_and_reset_policy_contract()
    print("PASS: reset/fault reasons preserve fail-safe state and START-only re-arm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
