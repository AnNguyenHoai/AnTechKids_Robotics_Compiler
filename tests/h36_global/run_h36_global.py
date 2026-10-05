#!/usr/bin/env python3
"""Regression coverage for global declarations in user-defined functions."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))

from compiler.compiler import RobotCompiler
from compiler.error import CompilerError
from compiler.generated.opcode import Opcode


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def compile_source(source: str) -> RobotCompiler:
    compiler = RobotCompiler()
    compiler.compile_ast(ast.parse(source))
    return compiler


def main() -> int:
    compiler = compile_source(
        """
sensor1 = 0
sensor2 = 0
sensor3 = 0

def update_sensors():
    global sensor1, sensor2, sensor3
    sensor1 = 1
    sensor2 = 2
    sensor3 = sensor1

update_sensors()
"""
    )

    bindings = compiler.global_scope.variables
    check("three student globals are allocated", all(name in bindings for name in ("sensor1", "sensor2", "sensor3")))
    check("sensor globals keep stable slots", [bindings[name] for name in ("sensor1", "sensor2", "sensor3")] == [0, 1, 2])

    instructions = compiler.program.instructions
    global_writes = [
        ins for ins in instructions
        if Opcode(ins.opcode) == Opcode.LoadConst and ins.p1 in {0, 1, 2}
    ]
    check("function writes target existing global slots", any(ins.p1 == 0 and ins.p2 == 1 for ins in global_writes) and any(ins.p1 == 1 and ins.p2 == 2 for ins in global_writes))
    check("global-to-global assignment uses the global destination", any(Opcode(ins.opcode) == Opcode.Store and ins.p1 == 0 and ins.p2 == 2 for ins in instructions))

    shadow = compile_source(
        """
value = 1

def local_write():
    value = 2

local_write()
"""
    )
    check("assignment without global remains local", shadow.global_scope.variables["value"] == 0 and shadow.global_scope.next_index >= 2)

    try:
        compile_source(
            """
def invalid():
    value = 1
    global value

invalid()
"""
        )
    except (CompilerError, SyntaxError) as exc:
        check("invalid declaration order is rejected", "global" in str(exc).lower())
    else:
        raise AssertionError("invalid declaration order is rejected")

    print("R4-MAINT-GLOBAL-01 Function Global Support: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
