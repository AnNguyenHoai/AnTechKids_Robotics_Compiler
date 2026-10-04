#!/usr/bin/env python3
"""Regression gate for Python bool constants leaking into generated C++."""
from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))

from compiler.compiler import RobotCompiler
from compiler.emitter import HeaderEmitter
from compiler.generated.opcode import Opcode


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    source = """
flag = True
disabled = False
if True:
    flag = False
forward(True)
"""
    compiler = RobotCompiler()
    program = compiler.compile_ast(ast.parse(source))

    operands = []
    for ins in program.instructions:
        operands.extend((ins.p1, ins.p2, ins.p3, ins.p4))

    check(
        "instruction IR contains no Python bool operands",
        not any(isinstance(value, bool) for value in operands),
    )

    load_values = [
        ins.p2 for ins in program.instructions
        if Opcode(ins.opcode) == Opcode.LoadConst
    ]
    check("True constants canonicalize to integer 1", 1 in load_values)
    check("False constants canonicalize to integer 0", 0 in load_values)

    with tempfile.TemporaryDirectory() as tmp:
        header = Path(tmp) / "program.h"
        HeaderEmitter().emit(program, header)
        generated = header.read_text(encoding="utf-8")

    check("generated C++ does not contain Python True literal", "True" not in generated)
    check("generated C++ does not contain Python False literal", "False" not in generated)
    check("generated C++ still contains LoadConst instructions", "Opcode::LoadConst" in generated)

    print("R4-MAINT-BOOL-01 Boolean Constant Codegen: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
