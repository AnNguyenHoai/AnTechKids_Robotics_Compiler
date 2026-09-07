#!/usr/bin/env python3
"""H29-D Function Semantics regression suite."""

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


def expect_error(name: str, source: str, expected: str):
    try:
        compile_source(source)
    except CompilerError as exc:
        message = str(exc)
        assert expected in message, (
            f"{name}: expected error containing {expected!r}, got {message!r}"
        )
        print(f"PASS: {name}")
        return
    raise AssertionError(f"{name}: compilation unexpectedly succeeded")


def opcode_names(program):
    return [Opcode(ins.opcode).name for ins in program.instructions]


def test_function_local_shadowing_does_not_modify_global():
    program = compile_source("""
x = 10
def foo():
    x = 20
    forward(x)
foo()
forward(x)
""")

    names = opcode_names(program)
    assert names == ["LoadConst", "LoadConst", "Forward", "Forward"], names
    # Global x is index 0; function-local x must use a distinct program-global
    # slot so the inline expansion cannot overwrite the global binding.
    assert program.instructions[0].p1 == 0
    assert program.instructions[0].p2 == 10
    assert program.instructions[1].p1 == 1
    assert program.instructions[1].p2 == 20
    assert program.instructions[2].p1 == 1
    assert program.instructions[3].p1 == 0
    print("PASS: function local variable shadows global without overwrite")


def test_function_can_read_global_variable():
    program = compile_source("""
speed = 60
def move():
    forward(speed)
move()
""")
    assert opcode_names(program) == ["LoadConst", "Forward"]
    assert program.instructions[1].p1 == 0
    print("PASS: function resolves global variable through parent scope")


def test_function_locals_are_isolated_between_calls():
    program = compile_source("""
def foo():
    x = 20
    forward(x)
foo()
foo()
""")
    names = opcode_names(program)
    assert names == ["LoadConst", "Forward", "LoadConst", "Forward"], names
    first_local = program.instructions[0].p1
    second_local = program.instructions[2].p1
    assert first_local != second_local, (
        f"Each inline function invocation needs an isolated local slot: "
        f"first={first_local}, second={second_local}"
    )
    assert program.instructions[1].p1 == first_local
    assert program.instructions[3].p1 == second_local
    print("PASS: repeated function calls get isolated local slots")


def test_function_break_is_rejected_at_definition():
    expect_error(
        "function break unsupported",
        "def foo():\n    break\n",
        "cannot use break",
    )


def test_function_continue_is_rejected_at_definition():
    expect_error(
        "function continue unsupported",
        "def foo():\n    continue\n",
        "cannot use continue",
    )


def test_function_break_cannot_leak_into_caller_loop():
    expect_error(
        "function break cannot control caller loop",
        "def foo():\n    break\nfor i in range(2):\n    foo()\n",
        "cannot use break",
    )


def test_function_can_have_own_loop():
    program = compile_source("""
def foo():
    for i in range(2):
        forward(20)
foo()
""")
    names = opcode_names(program)
    assert names.count("CompareLT") == 1
    assert names.count("Forward") == 1
    assert names.count("Add") == 1
    print("PASS: function owns its loop control-flow context")


def test_function_can_be_called_before_definition():
    program = compile_source("""
foo()
def foo():
    forward(50)
""")
    assert opcode_names(program) == ["LoadConst", "Forward"]
    print("PASS: function call before definition remains supported")


def test_nested_function_is_rejected():
    expect_error(
        "nested function unsupported",
        "def outer():\n    def inner():\n        pass\n",
        "Nested function definitions are not supported",
    )


def test_function_parameters_are_rejected():
    expect_error(
        "function parameters unsupported",
        "def foo(speed):\n    forward(speed)\n",
        "with parameters is not supported",
    )


def test_function_return_is_rejected():
    expect_error(
        "function return unsupported",
        "def foo():\n    return\n",
        "cannot use return",
    )


def test_duplicate_function_definition_is_rejected():
    expect_error(
        "duplicate function definition",
        "def foo():\n    pass\ndef foo():\n    pass\n",
        "Duplicate function definition",
    )


def test_user_function_cannot_be_expression_value():
    expect_error(
        "user function value unsupported",
        "def foo():\n    pass\nx = foo()\n",
        "cannot be used as a value",
    )


def main() -> int:
    test_function_local_shadowing_does_not_modify_global()
    test_function_can_read_global_variable()
    test_function_locals_are_isolated_between_calls()
    test_function_break_is_rejected_at_definition()
    test_function_continue_is_rejected_at_definition()
    test_function_break_cannot_leak_into_caller_loop()
    test_function_can_have_own_loop()
    test_function_can_be_called_before_definition()
    test_nested_function_is_rejected()
    test_function_parameters_are_rejected()
    test_function_return_is_rejected()
    test_duplicate_function_definition_is_rejected()
    test_user_function_cannot_be_expression_value()
    print("H29-D function semantics: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
