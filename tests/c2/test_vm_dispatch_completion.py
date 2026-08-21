#!/usr/bin/env python3
"""C2 VM dispatch completion checks.

These tests validate the live compiler -> opcode -> ESP32 VM contract for
LineMillisecond without requiring an ESP32/PlatformIO toolchain.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "robot-compiler"))

from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode


def test_compiler_emits_line_millisecond():
    source = "line_millisecond(50, 100)\n"
    program = RobotCompiler().compile_ast(ast.parse(source))

    instructions = [i for i in program.instructions if i.opcode != Opcode.LoadConst.value]
    assert len(instructions) == 1
    ins = instructions[0]
    assert ins.opcode == Opcode.LineMillisecond.value
    assert ins.p1 != ins.p2


def test_esp32_vm_dispatch_exists():
    vm_path = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
    text = vm_path.read_text(encoding="utf-8")
    assert "case Opcode::LineMillisecond:" in text
    assert "RobotAPI::LineMillisecond(" in text


def test_robot_api_contract_exists():
    header = ROOT / "robot-platform" / "main" / "src" / "Services" / "Robot" / "RobotAPI.h"
    cpp = ROOT / "robot-platform" / "main" / "src" / "Services" / "Robot" / "RobotAPI.cpp"
    h = header.read_text(encoding="utf-8")
    c = cpp.read_text(encoding="utf-8")
    assert "void LineMillisecond(int speed, int millisecond);" in h
    assert re.search(r"void\s+LineMillisecond\s*\(\s*int\s+speed\s*,\s*int\s+millisecond\s*\)", c)


def test_no_c2_dead_dispatch_cases_required():
    vm_path = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
    text = vm_path.read_text(encoding="utf-8")
    for opcode in (
        "MoveInitialize", "MoveRunAngle", "GetLightSensorData",
        "SetSeeringEngine", "SetSeeringEngineTime", "SetMotor",
        "SetMotorServo", "LineSetInitialize", "SetLizard",
        "UpdateVar", "DisplayVariable",
    ):
        assert f"case Opcode::{opcode}:" not in text


if __name__ == "__main__":
    tests = [
        test_compiler_emits_line_millisecond,
        test_esp32_vm_dispatch_exists,
        test_robot_api_contract_exists,
        test_no_c2_dead_dispatch_cases_required,
    ]
    failed = []
    for test in tests:
        try:
            test()
            print(f"{test.__name__}: PASS")
        except Exception as exc:
            failed.append((test.__name__, str(exc)))
            print(f"{test.__name__}: FAIL - {exc}")
    raise SystemExit(1 if failed else 0)
