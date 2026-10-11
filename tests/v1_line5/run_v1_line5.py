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
    mixer = (ROOT / "robot-platform/main/src/Services/Line/MotorMixer.cpp").read_text(encoding="utf-8")
    follower_state = (ROOT / "robot-platform/main/src/Services/Line/FollowerStateMachine.cpp").read_text(encoding="utf-8")
    recovery = (ROOT / "robot-platform/main/src/Services/Line/RecoveryStrategy.cpp").read_text(encoding="utf-8")
    intersection = (ROOT / "robot-platform/main/src/Services/Line/IntersectionDetector.cpp").read_text(encoding="utf-8")
    diagnostics = (ROOT / "robot-platform/main/src/Diagnostics/DiagnosticsManager.cpp").read_text(encoding="utf-8")
    console = (ROOT / "robot-platform/main/src/Diagnostics/Console/DevelopmentConsole.cpp").read_text(encoding="utf-8")
    serial = (ROOT / "robot-platform/main/src/Communication/SerialCommandHandler.cpp").read_text(encoding="utf-8")
    sensor_spec = (ROOT / "robot-docs/ROBOTAPI_SENSOR_SPEC.md").read_text(encoding="utf-8")
    platform_api = (ROOT / "robot-docs/ROBOT_PLATFORM_API.md").read_text(encoding="utf-8")
    motor_mapper = (ROOT / "robot-platform/main/src/Services/Robot/MotorOutputMapper.cpp").read_text(encoding="utf-8")

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
    require(follower, "_pid.update(controlError)", "PID consumes deadbanded Line5 error")
    require(follower, "CONTROL_DEADBAND = 0.20f", "Line5 center deadband")
    require(follower, "STEER_CONFIRM_TICKS = 2", "two-tick steering persistence")
    require(follower, "SPEED_FACTOR_MILD = 0.85f", "mild progressive speed schedule")
    require(follower, "SPEED_FACTOR_MEDIUM = 0.70f", "medium progressive speed schedule")
    require(follower, "SPEED_FACTOR_STRONG = 0.60f", "strong progressive speed schedule")
    require(follower, "_pendingSteerTicks", "steering persistence state")
    require(follower, "scheduleError", "progressive speed scheduling input")
    require(mixer, "baseSpeed + delta", "positive correction speeds up left wheel")
    require(mixer, "baseSpeed - delta", "positive correction slows right wheel")
    require(follower_state, "LINE_LOST_DEBOUNCE_MS = 40", "40ms transient line-loss debounce")
    require(follower_state, "_zeroMaskPending", "zero-mask debounce state")
    require(follower, "if (mask != 0)", "short dropout holds last valid filtered error")
    require(follower, "GAP_DIRECTIONAL_THRESHOLD = 0.25f", "center-gap directional threshold")
    require(follower, "SHARP_CORNER_HOLD_MS = 350", "bounded sharp-corner continuation")
    require(follower, "sharpLeftObserved", "far-left sharp-corner detection")
    require(follower, "sharpRightObserved", "far-right sharp-corner detection")
    require(follower, "continueThroughCornerGap", "FAR-to-zero sharp-corner continuation")
    require(follower, "leftMotor = 0;", "ambiguous center-gap brake")
    require(follower, "rightMotor = 0;", "ambiguous center-gap brake")
    require(robot_api, "LINE_CONTROL_TICK_MS = 5", "firmware-owned 5ms Line5 cadence")
    require(robot_api, "LINE_CONTROL_LEASE_MS = 120", "bounded Line5 command lease")
    require(robot_api, "_runLineControlTick(g_lineControlSpeed)", "background Line5 control tick")
    require(robot_api, "_lineLeaseExpired(nowMs)", "Line5 lease expiry")
    require(robot_api, "g_motionControlMode == MotionControlMode::Line && g_lineControlActive", "direct-motor Line5 ownership release")
    require(robot_api, "void setMotorsRawDiagnostic(int left, int right)", "raw motor diagnostic API")
    require(robot_api, "_setMotorsRaw(rawLeft, rawRight)", "raw motor diagnostic bypasses mapping")
    require(serial, 'input.startsWith("motor raw ")', "serial raw motor command")
    require(serial, "RobotAPI::setMotorsRawDiagnostic(left, right)", "serial raw motor command dispatch")
    assert "MotorOutputMapper::map(" not in robot_api[robot_api.index("void setMotorsRawDiagnostic"):robot_api.index("void setMotorsDirect")], "raw motor diagnostic must bypass mapper"
    require(follower, "if (recovering && !_wasRecovering)", "recovery phase resets on real LOST edge")
    require(recovery, "SOFT_INNER_SPEED = 0", "soft recovery true inner stop")
    require(recovery, "SOFT_OUTER_SPEED = 70", "reliable recovery outer speed")
    require(recovery, "SOFT_SEARCH_MS = 150", "short initial recovery pivot")
    require(recovery, "DEEP_SEARCH_SPEED = 70", "reliable deep recovery speed")
    assert "RECOVERY_BASE_SPEED = 80" not in recovery, "legacy immediate recovery spin still present"
    require(robot_api, "rawErr=%.2f filtErr=%.2f corr=%.2f", "Line5 tuning diagnostics")
    require(robot_api, "(unsigned long)loopDtUs", "Line5 response diagnostic loop timing argument")
    require(robot_api, "static void _setLineMotors", "line-specific pair-aware motor output path")
    require(robot_api, "MotorOutputMapper::mapSteeringPair", "Line5 pair-aware motor mapper usage")
    require(motor_mapper, "(void)speedScale;", "Line5 ignores global speedScale")
    require(motor_mapper, "(void)minDrive;", "Line5 ignores continuous minDrive remap")
    require(motor_mapper, "mapLineSide", "Line5 direct per-wheel mapping")
    assert "mapMagnitude(" not in motor_mapper[motor_mapper.index("void MotorOutputMapper::mapSteeringPair"):], "Line5 steering must not use general minDrive remap"
    require(robot_api, "LINE_START_BOOST_SPEED = 65", "measured Line5 startup boost")
    require(robot_api, "LINE_START_BOOST_MS = 60", "bounded Line5 startup boost")
    require(robot_api, "g_lineStartupBoostUntilMs", "Line5 startup boost state")
    require(robot_api, "startupBoostActive", "Line5 startup boost application")
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


def test_motor_mixer_direction_contract() -> None:
    def mix(base: int, correction: float, scale: float = 12.0) -> tuple[int, int]:
        delta = round(correction * scale)
        left = max(-100, min(100, base + delta))
        right = max(-100, min(100, base - delta))
        return left, right

    left, right = mix(60, 1.0)
    assert left > right, f"Positive/right error must turn right: got L={left}, R={right}"

    left, right = mix(60, -1.0)
    assert left < right, f"Negative/left error must turn left: got L={left}, R={right}"

    left, right = mix(60, 0.0)
    assert left == right == 60, f"Zero error must drive straight: got L={left}, R={right}"


def test_pair_aware_motor_mapping_examples() -> None:
    def map_pair(left: int, right: int, left_scale: float = 1.0, right_scale: float = 1.0) -> tuple[int, int]:
        def side(logical: int, scale: float) -> int:
            if logical == 0:
                return 0
            magnitude = round(abs(logical) * max(0.0, scale))
            magnitude = max(0, min(100, magnitude))
            return -magnitude if logical < 0 else magnitude

        return side(left, left_scale), side(right, right_scale)

    # Line5 now preserves the logical speed domain directly.
    assert map_pair(60, 60) == (60, 60)
    assert map_pair(72, 48) == (72, 48)
    assert map_pair(48, 72) == (48, 72)
    assert map_pair(84, 36) == (84, 36)
    assert map_pair(-45, 45) == (-45, 45)

    # Global speedScale is intentionally not part of Line5 steering mapping.
    assert map_pair(60, 60) == (60, 60)


def test_line_motor_operating_region_contract() -> None:
    header = (ROOT / "robot-platform/main/src/Services/Robot/MotorOutputMapper.h").read_text(encoding="utf-8")
    mapper = (ROOT / "robot-platform/main/src/Services/Robot/MotorOutputMapper.cpp").read_text(encoding="utf-8")
    api = (ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp").read_text(encoding="utf-8")
    require(header, "class LineMotorOperatingPolicy", "Line-only stateful output policy")
    require(mapper, "LEFT_RUN_MIN = 40", "left measured run floor")
    require(mapper, "RIGHT_RUN_MIN = 50", "right measured run floor")
    require(mapper, "RESTART_BOOST_MS = 60", "bounded per-wheel restart")
    require(mapper, "INNER_STOP_THRESHOLD = 20", "strong-steering pivot threshold")
    require(mapper, "outer > innerFloor", "do not invert commanded yaw")
    require(mapper, "direction == 0", "preserve true stop")
    require(mapper, "wheel.direction != direction", "restart on direction reversal")
    require(mapper, "wheel.restartAtMs = nowMs", "bounded reversal kick reset")
    require(api, "g_lineMotorPolicy.apply(", "Line5 actuator policy invoked")
    require(api, "g_lineMotorPolicy.reset()", "Line5 policy reset at motion boundaries")
    assert "g_lineMotorPolicy.apply(" not in api[api.index("static void _setMotors("):api.index("static void _setLineMotors(")], "general Forward/Backward must stay unchanged")

    def sustainable(left: int, right: int) -> tuple[int, int]:
        if left == right == 0:
            return 0, 0
        if left and abs(left) == abs(right):
            common = max(abs(left), 50)
            return (-common if left < 0 else common), (-common if right < 0 else common)
        left_outer = abs(left) > abs(right)
        outer = max(abs(left if left_outer else right), 40 if left_outer else 50)
        inner = abs(right if left_outer else left)
        floor = 50 if left_outer else 40
        if 0 < inner < floor:
            inner = floor if inner >= 20 and outer > floor else 0
        lmag, rmag = (outer, inner) if left_outer else (inner, outer)
        return (-lmag if left < 0 else lmag), (-rmag if right < 0 else rmag)

    assert sustainable(60, 60) == (60, 60)
    assert sustainable(52, 32) == (52, 50)
    assert sustainable(32, 52) == (40, 52)
    assert sustainable(57, 45) == (57, 50)  # mild correction keeps inner spinning
    assert sustainable(45, 57) == (45, 57)  # left already above reliable floor
    assert sustainable(48, 40) == (48, 0)   # never invert requested right yaw
    assert sustainable(36, 24) == (40, 0)
    assert sustainable(24, 36) == (40, 50)
    assert sustainable(35, 35) == (50, 50)
    assert sustainable(-45, 45) == (-50, 50)
    assert sustainable(0, 60) == (0, 60)
    assert sustainable(60, 0) == (60, 0)
    assert sustainable(0, 0) == (0, 0)
    assert sustainable(65, 15) == (65, 0)
    assert sustainable(15, 65) == (0, 65)
    # Follow and recovery source policies must preserve restart on sign change.


def test_startup_boost_and_progressive_schedule() -> None:
    start_boost = 65

    def boost(value: int, active: bool) -> int:
        if not active or value == 0:
            return value
        sign = -1 if value < 0 else 1
        return sign * max(abs(value), start_boost)

    assert (boost(60, True), boost(60, True)) == (65, 65)
    assert (boost(60, False), boost(60, False)) == (60, 60)
    assert boost(0, True) == 0, "Sharp-turn inner wheel must remain a true stop"

    def scheduled_base(speed: int, error: float) -> int:
        e = abs(error)
        factor = 1.0
        if e > 1.25:
            factor = 0.60
        elif e > 0.75:
            factor = 0.70
        elif e > 0.20:
            factor = 0.85
        return round(speed * factor)

    assert scheduled_base(60, 0.0) == 60
    assert scheduled_base(60, 0.5) == 51
    assert scheduled_base(60, 1.0) == 42
    assert scheduled_base(60, 1.5) == 36


def test_two_tick_direction_persistence() -> None:
    stable = 0
    pending = 0
    ticks = 0

    def step(observed: int) -> tuple[int, int, int, bool]:
        nonlocal stable, pending, ticks
        confirmed = observed == stable
        if not confirmed:
            if observed == pending:
                ticks += 1
            else:
                pending = observed
                ticks = 1
            if ticks >= 2:
                stable = observed
                pending = 0
                ticks = 0
                confirmed = True
        else:
            pending = 0
            ticks = 0
        return stable, pending, ticks, confirmed

    # A single opposite-side sample cannot reverse steering.
    assert step(-1)[3] is False
    assert step(-1)[0] == -1
    assert step(1)[3] is False
    assert stable == -1
    assert step(1)[0] == 1


def test_sharp_corner_policy() -> None:
    FAR_LEFT = 0x10
    LEFT = 0x08
    CENTER = 0x04
    RIGHT = 0x02
    FAR_RIGHT = 0x01

    def sharp_left(mask: int) -> bool:
        return bool(mask & FAR_LEFT) and not bool(mask & (CENTER | RIGHT | FAR_RIGHT))

    def sharp_right(mask: int) -> bool:
        return bool(mask & FAR_RIGHT) and not bool(mask & (CENTER | LEFT | FAR_LEFT))

    # Edge-only and edge+adjacent patterns are sharp-corner evidence.
    assert sharp_left(FAR_LEFT)
    assert sharp_left(FAR_LEFT | LEFT)
    assert sharp_right(FAR_RIGHT)
    assert sharp_right(FAR_RIGHT | RIGHT)

    # Center/other-side evidence must prevent accidental sharp mode.
    assert not sharp_left(FAR_LEFT | CENTER)
    assert not sharp_right(FAR_RIGHT | CENTER)
    assert not sharp_left(FAR_LEFT | FAR_RIGHT)
    assert not sharp_right(FAR_LEFT | FAR_RIGHT)

    # The commanded sharp turn is a one-wheel pivot, preserving immediate yaw
    # without waiting for LOST debounce/recovery.
    speed = 60
    left_turn = (0, speed)
    right_turn = (speed, 0)
    assert left_turn == (0, 60)
    assert right_turn == (60, 0)


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
    test_motor_mixer_direction_contract()
    print("PASS: Line5 motor mixer steering direction")
    test_pair_aware_motor_mapping_examples()
    print("PASS: Line5 direct motor mapping examples")
    test_line_motor_operating_region_contract()
    print("PASS: Line5 motor operating region contract")
    test_startup_boost_and_progressive_schedule()
    print("PASS: Line5 startup boost and progressive speed schedule")
    test_two_tick_direction_persistence()
    print("PASS: Line5 two-tick steering persistence")
    test_sharp_corner_policy()
    print("PASS: Line5 sharp-corner policy")
    test_compiler_transport_channels_0_to_4()
    print("PASS: compiler transports read_line channels 0..4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
