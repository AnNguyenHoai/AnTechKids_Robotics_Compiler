from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
sys.path.insert(0, str(COMPILER_ROOT))

from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"Missing {label}: {needle}"


def test_source_contract() -> None:
    gpio = (ROOT / "robot-platform/main/src/HardwareAbstraction/GPIO.h").read_text(encoding="utf-8")
    tcrt_header = (ROOT / "robot-platform/main/src/Sensor/TCRT5000.h").read_text(encoding="utf-8")
    tcrt_driver_spec = (ROOT / "robot-docs/TCRT5000_DRIVER_SPEC.md").read_text(encoding="utf-8")
    sensor_id = (ROOT / "robot-platform/main/src/Sensor/SensorID.h").read_text(encoding="utf-8")
    layout = (ROOT / "robot-platform/main/src/Services/Line/LineSensorLayout.h").read_text(encoding="utf-8")
    robot_api = (ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp").read_text(encoding="utf-8")
    diagnostic = (ROOT / "robot-platform/main/src/Diagnostic/Diagnostic.cpp").read_text(encoding="utf-8")
    estimator = (ROOT / "robot-platform/main/src/Services/Line/LineErrorEstimator.cpp").read_text(encoding="utf-8")
    follower = (ROOT / "robot-platform/main/src/Services/Line/LineFollower.cpp").read_text(encoding="utf-8")
    follower_state = (ROOT / "robot-platform/main/src/Services/Line/FollowerStateMachine.cpp").read_text(encoding="utf-8")
    recovery = (ROOT / "robot-platform/main/src/Services/Line/RecoveryStrategy.cpp").read_text(encoding="utf-8")
    intersection = (ROOT / "robot-platform/main/src/Services/Line/IntersectionDetector.cpp").read_text(encoding="utf-8")
    diagnostics = (ROOT / "robot-platform/main/src/Diagnostics/DiagnosticsManager.cpp").read_text(encoding="utf-8")
    console = (ROOT / "robot-platform/main/src/Diagnostics/Console/DevelopmentConsole.cpp").read_text(encoding="utf-8")
    serial = (ROOT / "robot-platform/main/src/Communication/SerialCommandHandler.cpp").read_text(encoding="utf-8")
    sensor_spec = (ROOT / "robot-docs/ROBOTAPI_SENSOR_SPEC.md").read_text(encoding="utf-8")
    platform_api = (ROOT / "robot-docs/ROBOT_PLATFORM_API.md").read_text(encoding="utf-8")

    for needle in (
        "SENSOR_TRCT5000_FL_PIN  ROBOT_PIN_34",
        "SENSOR_TRCT5000_L_PIN   ROBOT_PIN_18",
        "SENSOR_TRCT5000_C_PIN   ROBOT_PIN_16",
        "SENSOR_TRCT5000_R_PIN   ROBOT_PIN_17",
        "SENSOR_TRCT5000_FR_PIN  ROBOT_PIN_35",
    ):
        require(gpio, needle, "Line5 GPIO ownership")

    require(tcrt_header, "threshold = LOW", "active-low TCRT5000 semantic default")
    require(tcrt_driver_spec, "active-low", "active-low TCRT5000 hardware documentation")
    require(tcrt_driver_spec, "`LOW` = line detected", "black-line LOW polarity documentation")

    require(sensor_id, "LineFarLeft", "far-left SensorID")
    require(sensor_id, "LineFarRight", "far-right SensorID")

    expected_channels = {
        0: "LineLeft",
        1: "LineCenter",
        2: "LineRight",
        3: "LineFarLeft",
        4: "LineFarRight",
    }
    for channel, name in expected_channels.items():
        require(layout, f"case {channel}: id = SensorID::{name};", f"channel {channel} mapping")

    expected_masks = {
        "MASK_FAR_LEFT": "0x10",
        "MASK_LEFT": "0x08",
        "MASK_CENTER": "0x04",
        "MASK_RIGHT": "0x02",
        "MASK_FAR_RIGHT": "0x01",
        "MASK_ALL": "0x1F",
    }
    for name, value in expected_masks.items():
        require(layout, name, f"{name} declaration")
        require(layout, value, f"{name} value")

    require(robot_api, "LineSensorLayout::sensorIdFromChannel(channel, id)", "centralized channel mapping")
    require(robot_api, "SensorID::LineFarLeft", "far-left RobotAPI registration/raw path")
    require(robot_api, "SensorID::LineFarRight", "far-right RobotAPI registration/raw path")
    require(robot_api, "LineSensorLayout::MASK_FAR_LEFT", "canonical FL raw bit")
    require(robot_api, "LineSensorLayout::MASK_FAR_RIGHT", "canonical FR raw bit")

    for weight in ("-2.0f", "-1.0f", "0.0f", "1.0f", "2.0f"):
        require(estimator, weight, f"weighted estimator {weight}")
    require(follower, "LineErrorEstimator::estimate(mask)", "mask-driven line follower")
    require(follower, "_pid(1.0f, 0.0f, 0.0f, 0.02f)", "P-only smooth-control baseline")
    require(follower, "ERROR_FILTER_ALPHA = 0.70f", "responsive Line5 error filter")
    require(follower, "_scaleFactor(12.0f)", "responsive Line5 motor mixer scale")
    require(follower, "_pid.update(_filteredError)", "PID consumes filtered Line5 error")
    require(follower_state, "LINE_LOST_DEBOUNCE_MS = 40", "40ms transient line-loss debounce")
    require(follower_state, "_zeroMaskPending", "zero-mask debounce state")
    require(follower, "if (mask != 0)", "short dropout holds last valid filtered error")
    require(follower, "if (recovering && !_wasRecovering)", "recovery phase resets on real LOST edge")
    require(recovery, "SOFT_INNER_SPEED = 25", "soft recovery inner wheel speed")
    require(recovery, "SOFT_OUTER_SPEED = 65", "soft recovery outer wheel speed")
    require(recovery, "SOFT_SEARCH_MS = 300", "soft recovery duration")
    require(recovery, "DEEP_SEARCH_SPEED = 45", "deep recovery escalation speed")
    assert "RECOVERY_BASE_SPEED = 80" not in recovery, "legacy immediate recovery spin still present"
    require(robot_api, "rawErr=%.2f filtErr=%.2f corr=%.2f", "Line5 tuning diagnostics")
    assert "analogRead(34)" not in diagnostic, "GPIO34 must remain exclusively owned by LineFarLeft"
    require(diagnostic, "Battery check: SKIPPED", "battery diagnostic skips unowned ADC path")
    require(follower, "LAST_DIRECTION_THRESHOLD = 0.25f", "recovery direction threshold")
    require(intersection, "LineSensorLayout::isIntersectionCandidate", "5CH intersection candidate")
    assert "_history[i] == 0b111" not in intersection, "3CH intersection equality still present"

    for text, label in ((diagnostics, "diagnostics"), (console, "development console"), (serial, "serial diagnostics")):
        require(text, "SensorID::LineFarLeft", f"far-left {label}")
        require(text, "SensorID::LineFarRight", f"far-right {label}")
    require(console, "LineSensorLayout::MASK_FAR_LEFT", "canonical console FL mask")
    require(console, "LineSensorLayout::MASK_FAR_RIGHT", "canonical console FR mask")

    require(sensor_spec, "0=L, 1=C, 2=R, 3=FL, 4=FR", "sensor API channel documentation")
    require(sensor_spec, "bit4  bit3  bit2  bit1  bit0", "sensor API raw-mask documentation")
    require(platform_api, "0=Left, 1=Center, 2=Right, 3=Far Left, 4=Far Right", "platform API channel documentation")
    require(platform_api, "5-bit mask: bit4=Far Left", "platform API raw-mask documentation")


def test_weighted_examples() -> None:
    weights = {0x10: -2.0, 0x08: -1.0, 0x04: 0.0, 0x02: 1.0, 0x01: 2.0}

    def estimate(mask: int) -> float:
        active = [weight for bit, weight in weights.items() if mask & bit]
        return sum(active) / len(active) if active else 0.0

    expected = {
        0b10000: -2.0,
        0b11000: -1.5,
        0b01000: -1.0,
        0b01100: -0.5,
        0b00100: 0.0,
        0b00110: 0.5,
        0b00010: 1.0,
        0b00011: 1.5,
        0b00001: 2.0,
        0b00000: 0.0,
    }
    for mask, value in expected.items():
        actual = estimate(mask)
        assert actual == value, f"mask {mask:05b}: expected {value}, got {actual}"


def test_compiler_transport_channels_0_to_4() -> None:
    source = "\n".join(f"line_{channel} = read_line({channel})" for channel in range(5)) + "\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "line5_compile.py"
        path.write_text(source, encoding="utf-8")
        program = RobotCompiler(target="esp32").compile(path)

    read_line_ops = [ins for ins in program.instructions if ins.opcode == Opcode.ReadLine.value]
    assert len(read_line_ops) == 5, f"Expected 5 ReadLine opcodes, got {len(read_line_ops)}"


def main() -> int:
    test_source_contract()
    print("PASS: Line5 source/docs/diagnostics contract")
    test_weighted_examples()
    print("PASS: Line5 weighted estimator examples")
    test_compiler_transport_channels_0_to_4()
    print("PASS: compiler transports read_line channels 0..4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
