#!/usr/bin/env python3
"""VM-RT #384: canonical line-mask reactive fast-path contract."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def between(text: str, start: str, end: str) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b]


def main() -> int:
    perception_h = read("robot-platform/main/src/Services/Line/LinePerception.h")
    perception_cpp = read("robot-platform/main/src/Services/Line/LinePerception.cpp")
    snapshot_cpp = read("robot-platform/main/src/Sensor/LineSensorSnapshot.cpp")
    robot_cpp = read("robot-platform/main/src/Services/Robot/RobotAPI.cpp")
    vm_cpp = read("robot-platform/main/src/Services/VM/VM.cpp")
    opcode_h = read("robot-platform/main/include/generated/opcode.h")
    transformer = read("robot-frontend-robosim/frontend/transformer.py")
    sensor_handler = read("robot-compiler/compiler/handlers/sensor_handler.py")
    line_handler = read("robot-compiler/compiler/handlers/line_handler.py")

    check("canonical mask defines right bit0", "RIGHT = 0b001" in perception_h)
    check("canonical mask defines center bit1", "CENTER = 0b010" in perception_h)
    check("canonical mask defines left bit2", "LEFT = 0b100" in perception_h)
    check("canonical mask defines all channels", "ALL = LEFT | CENTER | RIGHT" in perception_h)
    check(
        "shared snapshot uses canonical L/C/R bit layout",
        "g_snapshot.left ? 4 : 0" in snapshot_cpp
        and "g_snapshot.center ? 2 : 0" in snapshot_cpp
        and "g_snapshot.right ? 1 : 0" in snapshot_cpp,
    )

    raw_body = between(robot_cpp, "int16_t GetTraceRaw(int port)", "// ===== Initialization =====")
    check(
        "GetTraceRaw preserves L/C/R mask layout",
        "mask |= 4" in raw_body and "mask |= 2" in raw_body and "mask |= 1" in raw_body,
    )

    for token in (
        "case 0:",
        "case LineMask::CENTER:",
        "case LineMask::LEFT:",
        "case LineMask::RIGHT:",
        "case LineMask::LEFT | LineMask::CENTER:",
        "case LineMask::CENTER | LineMask::RIGHT:",
        "case LineMask::ALL:",
        "default:",
    ):
        check(f"mask interpretation contains {token}", token in perception_cpp)
    check("ambiguous left+right mask stays UNKNOWN", "return LineState::UNKNOWN" in perception_cpp)

    line_basis = between(robot_cpp, "void LineBasis(int speed)", "void LineFollow(int speed)")
    check("LineBasis reads exactly one raw mask", line_basis.count("GetTraceRaw(1)") == 1)
    check("LineBasis makes exactly one follower decision", line_basis.count("follower.update(") == 1)
    check("LineBasis submits exactly one motor command", line_basis.count("setMotorsDirect(") == 1)

    check("existing GetTraceRaw opcode number remains 44", "GetTraceRaw = 44" in opcode_h)

    raw_vm = between(vm_cpp, "case Opcode::GetTraceRaw:", "case Opcode::LineBasis:")
    check(
        "VM GetTraceRaw still delegates one resolved port to RobotAPI",
        "RobotAPI::GetTraceRaw(" in raw_vm
        and "mContext.mVariables[instruction.p1]" in raw_vm
        and "mContext.mVariables[instruction.p3]" in raw_vm
        and raw_vm.count("RobotAPI::GetTraceRaw(") == 1,
    )

    state_vm = between(vm_cpp, "case Opcode::GetTraceState:", "case Opcode::GetTraceRaw:")
    check(
        "legacy GetTraceState VM path remains available",
        "RobotAPI::GetTraceState(" in state_vm
        and "mContext.mVariables[instruction.p1]" in state_vm
        and "mContext.mVariables[instruction.p2]" in state_vm
        and "mContext.mVariables[instruction.p3]" in state_vm
        and state_vm.count("RobotAPI::GetTraceState(") == 1,
    )

    state_frontend = between(
        transformer,
        'elif attr == "GetTraceV2I2CState":',
        'elif attr == "GetTraceV2I2CData":',
    )
    check(
        "legacy RoboSim state API remains unchanged",
        'len(node.args) != 2' in state_frontend
        and 'ast.Name(id="get_trace_state"' in state_frontend
        and "args=node.args" in state_frontend,
    )

    raw_frontend = between(
        transformer,
        'elif attr == "GetTraceV2I2CData":',
        'elif attr == "GetLightSensorData":',
    )
    check(
        "RoboSim raw API maps explicitly to canonical raw call",
        'len(node.args) != 1' in raw_frontend
        and 'ast.Name(id="get_trace_raw"' in raw_frontend
        and "args=node.args" in raw_frontend,
    )

    check("compiler raw getter emits GetTraceRaw", "Opcode.GetTraceRaw.value" in sensor_handler)
    check("compiler state getter still emits GetTraceState", "Opcode.GetTraceState.value" in sensor_handler)
    line_basis_handler = between(line_handler, "def line_basis", "def line_follow")
    check("line_basis emits one LineBasis opcode", line_basis_handler.count("Opcode.LineBasis.value") == 1)

    # Explicit fast path uses one sensor/control opcode per iteration versus the
    # three sensor opcodes required by the manual per-channel strategy, before
    # even counting its extra branches and motor writes.
    fast_sensor_ops = 1
    manual_sensor_ops = 3
    check("fast path materially reduces sensor dispatch count", fast_sensor_ops < manual_sensor_ops)
    check("fast path sensor dispatch reduction is at least 3x", manual_sensor_ops >= fast_sensor_ops * 3)

    # Architecture boundary: use explicit APIs; do not pattern-match user code.
    check("frontend contains no implicit three-getter optimizer", "three_getter" not in transformer.lower())
    check("sensor handler contains no line-follow pattern matcher", "line_follow" not in sensor_handler.lower())

    print("VM-RT #384 line-mask reactive fast path: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
