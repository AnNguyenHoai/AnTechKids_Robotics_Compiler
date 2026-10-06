from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
sys.path.insert(0, str(ROOT / "robostudio"))
sys.path.insert(0, str(COMPILER_ROOT))

from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode
from domain.hardware_config import HardwareConfig
from domain.hardware_requirement_validator import HardwareRequirementValidator
from domain.hardware_requirements import HardwareRequirementRegistry

API_H = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.h"
API_CPP = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
LAYOUT = ROOT / "robot-platform/main/src/Services/Line/LineSensorLayout.h"
SENSOR_SPEC = ROOT / "robot-docs/ROBOTAPI_SENSOR_SPEC.md"
PLATFORM_API = ROOT / "robot-docs/ROBOT_PLATFORM_API.md"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"Missing {label}: {needle}"


def test_public_signatures_are_stable() -> None:
    header = API_H.read_text(encoding="utf-8")
    required = (
        "int16_t ReadLine(int channel);",
        "int16_t GetTraceValue(int port, int channel);",
        "bool GetTraceState(int port, int channel);",
        "int16_t GetTraceRaw(int port);",
        "void LineBasis(int speed);",
        "void LineFollow(int speed);",
        "void LineMillisecond(int speed, int millisecond);",
        "void LineStop();",
        "void LineIntersectionStop(int speed, int type);",
        "void LineTurnEncounterLine(int speed, int angle, int direction);",
        "void LineForBmp(int speed, int degree);",
    )
    for signature in required:
        require(header, signature, f"public signature {signature}")


def test_channel_and_raw_mask_contract() -> None:
    layout = LAYOUT.read_text(encoding="utf-8")
    expected_channels = {
        0: "LineLeft",
        1: "LineCenter",
        2: "LineRight",
        3: "LineFarLeft",
        4: "LineFarRight",
    }
    for channel, name in expected_channels.items():
        require(layout, f"case {channel}: id = SensorID::{name};", f"channel {channel}")

    expected_masks = {
        "MASK_FAR_LEFT": "0x10",
        "MASK_LEFT": "0x08",
        "MASK_CENTER": "0x04",
        "MASK_RIGHT": "0x02",
        "MASK_FAR_RIGHT": "0x01",
        "MASK_ALL": "0x1F",
    }
    for name, value in expected_masks.items():
        require(layout, name, name)
        require(layout, value, f"{name} value")


def test_robotapi_uses_canonical_line_bank_boundary() -> None:
    api = API_CPP.read_text(encoding="utf-8")
    require(api, "g_lineSensorBank.readMask", "LineSensorBank acquisition")

    raw_start = api.index("int16_t GetTraceRaw(int port)")
    raw_end = api.index("// ===== Initialization =====", raw_start)
    raw = api[raw_start:raw_end]
    assert raw.count("g_lineSensorBank.readMask(") == 1
    assert "SensorManager::instance()" not in raw
    assert "SENSOR_TRCT5000_" not in api

    # Public channel reads still route through the frozen central channel map.
    read_start = api.index("int16_t ReadLine(int channel)")
    read_end = api.index("// ================================================================", read_start)
    read = api[read_start:read_end]
    require(read, "LineSensorLayout::sensorIdFromChannel(channel, id)", "ReadLine central channel mapping")

    trace_start = api.index("int16_t GetTraceValue(int port, int channel)")
    trace_end = api.index("int16_t GetTraceRaw(int port)", trace_start)
    trace = api[trace_start:trace_end]
    require(trace, "LineSensorLayout::sensorIdFromChannel(channel, id)", "trace central channel mapping")


def test_feature_off_behavior_stays_neutral() -> None:
    api = API_CPP.read_text(encoding="utf-8")
    required_guards = (
        ("int16_t GetTraceValue", "return 0;"),
        ("bool GetTraceState", "return false;"),
        ("int16_t GetTraceRaw", "return 0;"),
        ("void LineBasis", "Line feature disabled by hardware configuration"),
    )
    for fn, marker in required_guards:
        start = api.index(fn)
        end = api.find("\n}", start)
        body = api[start:end + 2]
        require(body, "#if !ROBOT_FEATURE_LINE_SENSOR", f"{fn} feature guard")
        require(body, marker, f"{fn} disabled behavior")


def test_compiler_transports_all_five_read_line_channels() -> None:
    source = "\n".join(f"line_{ch} = read_line({ch})" for ch in range(5)) + "\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "line5_public_api.py"
        path.write_text(source, encoding="utf-8")
        program = RobotCompiler().compile(path)

    ops = [ins for ins in program.instructions if ins.opcode == Opcode.ReadLine.value]
    assert len(ops) == 5, f"Expected five ReadLine opcodes, got {len(ops)}"


def configured(**states):
    config = HardwareConfig.create_default()
    for device_id, enabled in states.items():
        config.set_enabled(device_id, enabled)
    return config


def test_hardware_requirement_validator_contract() -> None:
    sensing = (
        "read_line", "get_trace_value", "get_trace_state", "get_trace_raw",
        "GetTraceValue", "GetTraceV2I2CChxState", "GetTraceRaw",
    )
    for name in sensing:
        assert HardwareRequirementRegistry.required_devices(name) == frozenset({"line_sensor"}), name

    behaviors = (
        "line_basis", "line_follow", "line_stop", "line_millisecond",
        "line_intersection_stop", "line_turn_encounterline", "line_for_bmp",
        "LineBasis", "LineFollow", "LineStop", "LineMillisecond",
        "LineIntersectionStop", "LineTurnEncounterLine", "LineForBmp",
    )
    for name in behaviors:
        assert HardwareRequirementRegistry.required_devices(name) == frozenset({"motor", "line_sensor"}), name

    disabled = configured(motor=True, line_sensor=False)
    result = HardwareRequirementValidator.validate(
        "import rcu\nrcu.line_follow(60)\n", disabled
    )
    assert not result.valid
    assert result.issues[0].disabled_devices == ("line_sensor",)

    enabled = configured(motor=True, line_sensor=True)
    assert HardwareRequirementValidator.validate(
        "import rcu\nrcu.line_follow(60)\n", enabled
    ).valid


def test_docs_match_frozen_public_contract() -> None:
    sensor = SENSOR_SPEC.read_text(encoding="utf-8")
    platform = PLATFORM_API.read_text(encoding="utf-8")
    require(sensor, "0=L, 1=C, 2=R, 3=FL, 4=FR", "sensor channel docs")
    require(sensor, "bit4  bit3  bit2  bit1  bit0", "sensor raw mask docs")
    require(platform, "0=Left, 1=Center, 2=Right, 3=Far Left, 4=Far Right", "platform channel docs")
    require(platform, "5-bit mask: bit4=Far Left", "platform raw mask docs")


def main() -> int:
    test_public_signatures_are_stable()
    print("PASS: public Line5 signatures remain stable")
    test_channel_and_raw_mask_contract()
    print("PASS: public channel IDs and canonical raw mask remain frozen")
    test_robotapi_uses_canonical_line_bank_boundary()
    print("PASS: RobotAPI hides MCP physical ordering behind canonical LineSensorBank")
    test_feature_off_behavior_stays_neutral()
    print("PASS: line feature OFF behavior remains deterministic")
    test_compiler_transports_all_five_read_line_channels()
    print("PASS: compiler transports read_line channels 0..4")
    test_hardware_requirement_validator_contract()
    print("PASS: Hardware Requirement Validator still enforces line_sensor")
    test_docs_match_frozen_public_contract()
    print("PASS: public documentation matches the frozen V1/V2 compatibility contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
