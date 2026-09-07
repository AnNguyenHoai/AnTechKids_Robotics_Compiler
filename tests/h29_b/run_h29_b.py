"""H29-B control-flow semantic regression tests."""

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
from compiler.ir import Opcode


def compile_source(source: str):
    return RobotCompiler().compile_ast(ast.parse(source))


def expect_error(name: str, source: str, expected: str):
    try:
        compile_source(source)
    except CompilerError as exc:
        if expected not in str(exc):
            raise AssertionError(
                f"{name}: expected error containing {expected!r}, got {str(exc)!r}"
            ) from exc
        print(f"PASS: {name}")
        return
    raise AssertionError(f"{name}: expected CompilerError")


def jump_targets(program, opcode_name: str):
    return [
        ins.operands[0]
        for ins in program.instructions
        if Opcode(ins.opcode).name == opcode_name
    ]


def increment_block_indices(program):
    """Return instruction indices that start the loop increment blocks."""
    # The current compiler emits the range increment as Add followed by the
    # loop-back jump. For nested loops the inner increment is emitted first.
    return [
        i
        for i, ins in enumerate(program.instructions)
        if Opcode(ins.opcode).name == "Add"
        and i + 1 < len(program.instructions)
        and Opcode(program.instructions[i + 1].opcode).name == "Jump"
    ]


def test_for_continue_targets_increment():
    program = compile_source("""
for i in range(3):
    if i == 1:
        continue
    forward(20)
""")

    increments = increment_block_indices(program)
    assert len(increments) == 1, f"Expected one loop increment, got {increments}"
    increment_start = increments[0]

    jumps = jump_targets(program, "Jump")
    assert increment_start in jumps, (
        f"Expected for-continue target {increment_start}, got {jumps}"
    )
    print("PASS: for continue reaches increment")


def test_for_break_exits_loop():
    program = compile_source("""
for i in range(3):
    if i == 1:
        break
    forward(20)
""")

    increments = increment_block_indices(program)
    assert len(increments) == 1, f"Expected one loop increment, got {increments}"
    loop_end = increments[0] + 2

    jumps = jump_targets(program, "Jump")
    assert loop_end in jumps, f"Expected break target {loop_end}, got {jumps}"
    print("PASS: for break exits current loop")


def test_nested_continue_targets_inner_loop():
    program = compile_source("""
for i in range(2):
    for j in range(3):
        if j == 1:
            continue
        forward(20)
""")

    increments = increment_block_indices(program)
    assert len(increments) == 2, f"Expected two loop increments, got {increments}"
    inner_increment_start = increments[0]
    outer_increment_start = increments[1]

    jumps = jump_targets(program, "Jump")
    assert inner_increment_start in jumps, (
        f"Expected inner continue target {inner_increment_start}, got {jumps}"
    )
    assert outer_increment_start not in jumps, (
        f"Inner continue must not target outer increment {outer_increment_start}; "
        f"Jump targets={jumps}"
    )
    print("PASS: nested continue targets current inner loop")


def test_while_continue_targets_condition():
    # x must be defined before the while condition. H29-B is testing control
    # flow here, not undefined-variable handling (which belongs to H29-A).
    program = compile_source("""
x = 2
while x > 0:
    if x == 1:
        continue
    forward(20)
""")

    jumps = jump_targets(program, "Jump")
    compare_indices = [
        i for i, ins in enumerate(program.instructions)
        if Opcode(ins.opcode).name == "CompareGT"
    ]
    assert compare_indices, "Expected while condition CompareGT"
    condition_target = compare_indices[0]
    assert condition_target in jumps, (
        f"while continue/loop-back must target condition {condition_target}; "
        f"Jump targets={jumps}"
    )
    print("PASS: while continue targets condition")


def main():
    expect_error("break outside loop", "break", "'break' is not inside a loop")
    expect_error("continue outside loop", "continue", "'continue' is not inside a loop")
    expect_error(
        "for-else unsupported",
        "for i in range(2):\n    forward(10)\nelse:\n    stop()",
        "for-else is not supported",
    )
    expect_error(
        "while-else unsupported",
        "x = 1\nwhile x > 0:\n    stop()\nelse:\n    stop()",
        "while-else is not supported",
    )

    test_for_continue_targets_increment()
    test_for_break_exits_loop()
    test_nested_continue_targets_inner_loop()
    test_while_continue_targets_condition()
    print("H29-B control-flow semantic correctness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
