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


def increment_block_indices(program):
    """Return LoadConst indices that immediately precede loop Add increments."""
    indices = []
    for i, ins in enumerate(program.instructions):
        if Opcode(ins.opcode).name == "Add" and i > 0:
            if Opcode(program.instructions[i - 1].opcode).name == "LoadConst":
                indices.append(i - 1)
    return indices


def test_for_continue_reaches_increment():
    program = compile_source("""
for i in range(3):
    if i == 1:
        continue
    forward(50)
""")

    # The continue label is immediately before the increment LoadConst. A
    # continue must jump there, then execute Add and only then loop back.
    increments = increment_block_indices(program)
    assert len(increments) == 1, f"Expected one loop increment, got {increments}"
    increment_start = increments[0]

    jumps = jump_targets(program, "Jump")
    assert increment_start in jumps, (
        "for/continue must jump to the loop increment block; "
        f"Jump targets={jumps}, increment start={increment_start}"
    )

    # The normal loop-back jump must still target the loop condition, before
    # the increment block.
    assert any(target < increment_start for target in jumps), (
        f"Expected a loop-back Jump before increment, got {jumps}"
    )
    print("PASS: for continue executes increment before next condition")


def test_for_break_targets_loop_end():
    program = compile_source("""
for i in range(3):
    if i == 1:
        break
    forward(50)
stop()
""")

    jumps = jump_targets(program, "Jump")
    assert jumps, "Expected Jump instructions for break/loop-back"

    # The loop end label is immediately before the statement following the
    # loop, so break must target the final Stop instruction in this fixture.
    end_target = len(program.instructions) - 1
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

    increments = increment_block_indices(program)
    assert len(increments) == 2, f"Expected two loop increments, got {increments}"

    jumps = jump_targets(program, "Jump")
    inner_increment_start = increments[0]
    outer_increment_start = increments[1]

    # Inner continue must land on the inner increment, not the outer loop's
    # increment block. The outer loop's increment is reached naturally after
    # the inner loop finishes.
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

    # A condition can require multiple instructions (for example, loading
    # the RHS constant) before its Compare opcode. Therefore the correct
    # target is the condition *entry label*, not necessarily the CompareGT
    # instruction itself.
    jumps = jump_targets(program, "Jump")
    compare_indices = [
        i for i, ins in enumerate(program.instructions)
        if Opcode(ins.opcode).name == "CompareGT"
    ]
    assert compare_indices, "Expected while condition CompareGT"

    compare_index = compare_indices[0]
    backward_jumps = [
        target
        for index, ins in enumerate(program.instructions)
        if Opcode(ins.opcode).name == "Jump"
        for target in [ins.p2]
        if target < index
    ]
    assert backward_jumps, "Expected while continue/loop-back backward Jump"

    condition_target = backward_jumps[0]
    assert all(target == condition_target for target in backward_jumps), (
        f"while continue/loop-back must share condition target {condition_target}; "
        f"Backward jump targets={backward_jumps}"
    )
    assert condition_target <= compare_index, (
        f"while condition target {condition_target} must enter before CompareGT "
        f"at {compare_index}"
    )
    print("PASS: while continue targets condition entry")


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
