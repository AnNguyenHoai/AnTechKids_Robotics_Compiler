#!/usr/bin/env python3
"""H29-B Control-flow Semantic Correctness regression suite."""

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


def compile_source(source: str):
    return RobotCompiler().compile_ast(ast.parse(source))


def op(program, index):
    return Opcode(program.instructions[index].opcode).name


def jump_targets(program, opcode_name):
    opcode = Opcode[opcode_name].value
    return [ins.p2 for ins in program.instructions if ins.opcode == opcode]


def expect_error(name: str, source: str, expected: str):
    try:
        compile_source(source)
    except CompilerError as exc:
        message = str(exc)
        if expected not in message:
            raise AssertionError(
                f"{name}: expected error containing {expected!r}, got {message!r}"
            )
        print(f"PASS: {name}")
        return
    raise AssertionError(f"{name}: compilation unexpectedly succeeded")


def test_for_continue_reaches_increment():
    program = compile_source("""
for i in range(3):
    if i == 1:
        continue
    forward(50)
""")

    # The for-loop increment is the Add instruction immediately following
    # the increment LoadConst. A continue must jump to that increment label,
    # never directly back to the loop condition.
    add_indices = [
        i for i, ins in enumerate(program.instructions)
        if Opcode(ins.opcode).name == "Add"
    ]
    assert len(add_indices) == 1, f"Expected one loop increment Add, got {add_indices}"
    increment_add = add_indices[0]

    jumps = jump_targets(program, "Jump")
    assert increment_add in jumps, (
        "for/continue must jump to the loop increment; "
        f"Jump targets={jumps}, increment Add={increment_add}"
    )

    # The normal loop-back jump must still target the loop condition, which
    # occurs before the increment block.
    assert any(target < increment_add for target in jumps), (
        f"Expected a loop-back Jump before increment, got {jumps}"
    )
    print("PASS: for continue executes increment before next condition")


def test_for_break_targets_loop_end():
    program = compile_source("""
for i in range(3):
    if i == 1:
        break
    forward(50)
""")

    jumps = jump_targets(program, "Jump")
    assert jumps, "Expected Jump instructions for break/loop-back"

    # The last instruction is the statement after the loop. Break must target
    # the instruction immediately after the loop body/increment block.
    end_target = len(program.instructions)
    assert end_target in jumps, (
        f"break must target loop end {end_target}; Jump targets={jumps}"
    )
    print("PASS: for break exits current loop")


def test_nested_continue_targets_inner_loop():
    program = compile_source("""
for i in range(2):
    for j in range(3):
        if j == 1:
            continue
        forward(10)
""")

    add_indices = [
        i for i, ins in enumerate(program.instructions)
        if Opcode(ins.opcode).name == "Add"
    ]
    assert len(add_indices) == 2, f"Expected two loop increments, got {add_indices}"

    jumps = jump_targets(program, "Jump")
    inner_increment = add_indices[0]
    outer_increment = add_indices[1]

    # Inner continue must land on the inner increment, not the outer loop.
    assert inner_increment in jumps, (
        f"Expected inner continue target {inner_increment}, got {jumps}"
    )
    assert outer_increment in jumps, (
        f"Expected outer loop-back target before/around increment, got {jumps}"
    )
    print("PASS: nested continue targets current inner loop")


def test_while_continue_targets_condition():
    program = compile_source("""
while x > 0:
    if x == 1:
        continue
    forward(20)
""")

    # The first label target used by JumpIfFalse is the while end; the
    # loop-back target is the instruction containing the while condition.
    jump_if_false_targets = jump_targets(program, "JumpIfFalse")
    jumps = jump_targets(program, "Jump")
    assert jump_if_false_targets, "Expected while condition JumpIfFalse"
    condition_target = min(
        i for i, ins in enumerate(program.instructions)
        if Opcode(ins.opcode).name == "CompareGT"
    )
    assert condition_target in jumps, (
        f"while continue/loop-back must target condition {condition_target}; "
        f"Jump targets={jumps}"
    )
    print("PASS: while continue targets condition")


def main() -> int:
    test_for_continue_reaches_increment()
    test_for_break_targets_loop_end()
    test_nested_continue_targets_inner_loop()
    test_while_continue_targets_condition()

    expect_error(
        "break outside loop",
        "break\n",
        "'break' outside loop.",
    )
    expect_error(
        "continue outside loop",
        "continue\n",
        "'continue' outside loop.",
    )
    expect_error(
        "for-else unsupported",
        "for i in range(3):\n    pass\nelse:\n    stop()\n",
        "For-else is not supported",
    )
    expect_error(
        "while-else unsupported",
        "while x > 0:\n    pass\nelse:\n    stop()\n",
        "While-else is not supported",
    )

    print("H29-B control-flow semantics: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
