#!/usr/bin/env python3
"""V1-S8-C: deterministic compiler/VM-ISA regression for the user Line7 program.

This executes a bounded subset of the *generated* ESP32 instructions against
synthetic five-eye values. It is NOT the ESP32 firmware or a physical test.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "robot-compiler"))
sys.path.insert(0, str(ROOT / "robot-frontend-robosim"))

from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode
from compiler.safety_validator import (
    _required_variable_indices, load_resource_contract, validate_program,
)
from frontend.rewriter import rewrite
from frontend.trace_channel_normalizer import ESP32_LINE5_PROJECTION

SOURCE = ROOT / "tests/v1_s8a/fixtures/user_line7_overflow.py"
LIMITS = load_resource_contract()
assert LIMITS["program"]["max_instructions"] == 512
assert LIMITS["runtime"]["max_variables"] == 128
assert [ESP32_LINE5_PROJECTION[i] for i in range(1, 8)] == [3, 3, 0, 1, 2, 4, 4]

with TemporaryDirectory() as td:
    path = Path(td) / "esp32_line5.py"
    rewrite(SOURCE, path, target="esp32")
    rewritten = ast.parse(path.read_text(encoding="utf-8"))
    channels = [
        call.args[1].value
        for call in ast.walk(rewritten)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "get_trace_state"
        and len(call.args) == 2
        and isinstance(call.args[1], ast.Constant)
    ]
    assert sorted(channels) == sorted([3, 3, 0, 1, 2, 4, 4]), channels
    program = RobotCompiler(target="esp32").compile(path)

assert not validate_program(program), [
    (v.rule, v.message) for v in validate_program(program)
]
variables = set()
for ins in program.instructions:
    variables.update(_required_variable_indices(
        int(ins.opcode), (ins.p1, ins.p2, ins.p3, ins.p4)
    ))
max_index = max(variables) if variables else -1
assert len(program.instructions) <= 512
assert max_index < 128
print(f"S8-C ESP32 Line5: {len(program.instructions)}/512 instructions, "
      f"variable span {max_index + 1}/128")

def first_line_decision(physical):
    """Run until initial motion and the first sensor-based motor decision."""
    regs = [0] * 128
    pc = 0
    motors = []
    reads = []
    for step in range(4000):
        if not 0 <= pc < len(program.instructions):
            raise AssertionError(f"PC escaped program: {pc}")
        ins = program.instructions[pc]
        op = Opcode(ins.opcode)
        if op == Opcode.LoadConst:
            regs[ins.p1] = ins.p2
        elif op == Opcode.Store:
            regs[ins.p2] = regs[ins.p1]
        elif op in (Opcode.CompareEQ, Opcode.CompareNE,
                    Opcode.CompareLT, Opcode.CompareLE,
                    Opcode.CompareGT, Opcode.CompareGE):
            a, b = regs[ins.p1], regs[ins.p2]
            funcs = {
                Opcode.CompareEQ: a == b,
                Opcode.CompareNE: a != b,
                Opcode.CompareLT: a < b,
                Opcode.CompareLE: a <= b,
                Opcode.CompareGT: a > b,
                Opcode.CompareGE: a >= b,
            }
            regs[ins.p3] = int(funcs[op])
        elif op == Opcode.GetTraceState:
            port, channel = regs[ins.p1], regs[ins.p2]
            assert port == 1 and 0 <= channel <= 4, (port, channel)
            regs[ins.p3] = int(physical[channel])
            reads.append(channel)
        elif op == Opcode.SetMotorSpeed:
            motors.append((regs[ins.p1], regs[ins.p2]))
            if len(motors) == 2:
                return motors, reads, step + 1
        elif op == Opcode.Wait:
            assert regs[ins.p1] >= 0
        elif op == Opcode.Jump:
            pc = ins.p2
            continue
        elif op == Opcode.JumpIfFalse:
            if not regs[ins.p1]:
                pc = ins.p2
                continue
        elif op == Opcode.JumpIfTrue:
            if regs[ins.p1]:
                pc = ins.p2
                continue
        else:
            raise AssertionError(f"Unexpected opcode {op.name} at PC={pc}")
        pc += 1
    raise AssertionError("No second motor decision within 4000 VM steps")

# Physical order: 0=Left, 1=Center, 2=Right, 3=Far Left, 4=Far Right.
cases = [
    ("center", {1: 1}, (70, 70)),
    ("left", {0: 1}, (40, 70)),
    ("right", {2: 1}, (70, 40)),
    ("far-left", {3: 1}, (0, 70)),
    ("far-right", {4: 1}, (70, 0)),
    ("center+left", {0: 1, 1: 1}, (-70, 70)),
    ("center+right", {1: 1, 2: 1}, (70, -70)),
    ("center+far-left", {1: 1, 3: 1}, (-70, 70)),
    ("center+far-right", {1: 1, 4: 1}, (70, -70)),
]
for name, raised, expected in cases:
    physical = {i: int(i in raised) for i in range(5)}
    motors, reads, steps = first_line_decision(physical)
    assert motors == [(50, 50), expected], (name, motors, expected)
    assert sorted(reads) == sorted([3, 3, 0, 1, 2, 4, 4]), (name, reads)
    print(f"PASS S8-C {name}: motors={motors}, steps={steps}")

# Not all-black/no-line is a movement decision in the source program:
# the fallback is pass, which preserves the previous motor command.
# Guard against accidentally claiming fail-safe braking here.
no_line = {i: 0 for i in range(5)}
regs = [0] * 128
print("NOTE S8-C: no-line fallback in source is pass (does NOT automatically stop motors)")
# Exercise the capacity increase independently of compiler optimizations.
# Jump over 299 intermediate instructions to PC=300, and write variable 127.
# This asserts 16-bit PC/size and widened variable indices in generated C++.
from compiler.program import Program
from compiler.emitter import HeaderEmitter
long_program = Program()
long_program.emit(Opcode.Jump.value, 0, 300)
for _ in range(299):
    long_program.emit(Opcode.LoadConst.value, 127, 23)
long_program.emit(Opcode.LoadConst.value, 127, 77)
long_program.emit(Opcode.Stop.value)
assert len(long_program.instructions) == 302
assert not validate_program(long_program)
with TemporaryDirectory() as td:
    output = Path(td) / "generated_program.h"
    HeaderEmitter().emit(long_program, output)
    header = output.read_text(encoding="utf-8")
    assert "const uint16_t generatedProgramSize = 302;" in header
    assert "Instruction(Opcode::Jump, 0, 300, 0, 0)" in header
    assert "Instruction(Opcode::LoadConst, 127, 77, 0, 0)" in header
assert [i.p2 for i in long_program.instructions if i.opcode == Opcode.Jump.value] == [300]
print("PASS S8-C 302-instruction generated firmware header, PC=300, var=127")

# Never allow an empty evidence template to be interpreted as acceptance.
from validate_physical_evidence import validate
valid, evidence_issues = validate(
    ROOT / "tests/v1_s8c/physical_evidence_TEMPLATE.csv"
)
assert not valid and evidence_issues
print("PASS S8-C physical evidence gate rejects empty, unverified template")
print("PASS S8-C bounded VM-ISA semantic regression (NOT physical acceptance)")
