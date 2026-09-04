
from pathlib import Path

from domain.device_registry import DeviceRegistry
from domain.hardware_requirements import HardwareRequirementRegistry


ROOT = Path(__file__).resolve().parents[2]
ROBOT_API_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "Robot" / "RobotAPI.cpp"
ROBOT_API_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "Robot" / "RobotAPI.h"
CAP_H = ROOT / "robot-platform" / "main" / "src" / "HardwareAbstraction" / "HardwareCapability.h"
CAP_CPP = ROOT / "robot-platform" / "main" / "src" / "HardwareAbstraction" / "HardwareCapability.cpp"


def test_capability_contract_covers_every_registered_device():
    header = CAP_CPP.read_text(encoding="utf-8")
    for device in DeviceRegistry.all():
        enum_name = {
            "motor": "Motor",
            "encoder": "Encoder",
            "line_sensor": "LineSensor",
            "ultrasonic": "Ultrasonic",
            "imu": "IMU",
            "servo": "Servo",
            "buzzer": "Buzzer",
        }[device.device_id]
        assert f"Device::{enum_name}" in header
        assert f"ROBOT_FEATURE_{device.device_id.upper()}" in header


def test_capability_contract_exposes_stable_runtime_query():
    header = CAP_H.read_text(encoding="utf-8")
    api = ROBOT_API_H.read_text(encoding="utf-8")
    assert "bool isEnabled(Device device);" in header
    assert "uint8_t mask();" in header
    assert "bool isHardwareEnabled(HardwareCapability::Device device);" in api
    assert "void printHardwareCapabilities();" in api


def test_disabled_actuator_contract_is_guarded_at_robot_api_boundary():
    source = ROBOT_API_CPP.read_text(encoding="utf-8")
    for fn in ("Forward", "Backward", "TurnLeft", "TurnRight", "SetMotorSpeed", "setMotorsDirect"):
        block = source[source.index(f"void {fn}("):]
        block = block[:block.index("\n}", 1) + 2]
        assert "#if !ROBOT_FEATURE_MOTOR" in block


def test_existing_sensor_fallback_contracts_remain_explicit():
    source = ROBOT_API_CPP.read_text(encoding="utf-8")
    assert "#if !ROBOT_FEATURE_ULTRASONIC" in source and "return -1;" in source
    assert "#if !ROBOT_FEATURE_LINE_SENSOR" in source and "return 0;" in source
    # Encoder APIs retain callable no-op/neutral fallbacks when disabled.
    assert "int64_t GetEncoderCount(int side)" in source
    assert "return 0;" in source


def test_requirement_registry_matches_registered_hardware_ids():
    ids = set(DeviceRegistry.ids())
    for api in HardwareRequirementRegistry.known_api_names():
        assert HardwareRequirementRegistry.required_devices(api).issubset(ids)
