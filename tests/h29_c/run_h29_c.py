#!/usr/bin/env python3
"""H29-C Expression Semantics regression suite."""

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


def opcode_names(program):
    return [Opcode(ins.opcode).name for ins in program.instructions]


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


def expect_opcode(name: str, source: str, expected: str):
    program = compile_source(source)
    names = opcode_names(program)
    assert expected in names, f"{name}: expected {expected}, got {names}"
    print(f"PASS: {name}")


def test_all_binary_comparisons():
    cases = [
        ("==", "CompareEQ"),
        ("!=", "CompareNE"),
        ("<", "CompareLT"),
        ("<=", "CompareLE"),
        (">", "CompareGT"),
        (">=", "CompareGE"),
    ]
    for operator, opcode in cases:
        expect_opcode(
            f"comparison {operator}",
            f"x = 2\ny = 3\nz = x {operator} y\n",
            opcode,
        )


def test_chained_comparison_is_rejected():
    expect_error(
        "chained comparison",
        "x = 1\ny = 2\nz = 3\nresult = x < y < z\n",
        "Chained comparisons are not supported",
    )


def test_comparison_inside_if_is_preserved():
    program = compile_source("""
x = 80
if x > 50:
    forward(20)
""")
    names = opcode_names(program)
    assert "CompareGT" in names, f"Expected CompareGT, got {names}"
    assert "JumpIfFalse" in names, f"Expected JumpIfFalse, got {names}"
    print("PASS: comparison inside if")


def test_boolean_and_compiles():
    program = compile_source("""
a = 1
b = 2
result = a < b and b > 0
""")
    names = opcode_names(program)
    assert names.count("JumpIfFalse") >= 2, (
        f"and expression must short-circuit each non-final operand, got {names}"
    )
    assert "CompareLT" in names and "CompareGT" in names, (
        f"Expected both comparison operands, got {names}"
    )
    print("PASS: boolean and expression")


def test_boolean_or_is_explicitly_rejected():
    expect_error(
        "boolean or",
        "a = 1\nb = 2\nresult = a > b or b > 0\n",
        "Unsupported boolean operator: Or",
    )


def test_unary_negation_compiles():
    expect_opcode(
        "unary negation",
        "x = 10\ny = -x\n",
        "Neg",
    )


def test_unsupported_unary_is_rejected():
    expect_error(
        "unary plus",
        "x = 10\ny = +x\n",
        "Unsupported unary operator: UAdd",
    )


def test_nested_expression_is_compiled_without_truncation():
    program = compile_source("""
a = 10
b = 3
c = 2
result = (a - b) * c
""")
    names = opcode_names(program)
    assert "Sub" in names, f"Expected Sub, got {names}"
    assert "Mul" in names, f"Expected Mul, got {names}"
    print("PASS: nested arithmetic expression")


def main() -> int:
    test_all_binary_comparisons()
    test_chained_comparison_is_rejected()
    test_comparison_inside_if_is_preserved()
    test_boolean_and_compiles()
    test_boolean_or_is_explicitly_rejected()
    test_unary_negation_compiles()
    test_unsupported_unary_is_rejected()
    test_nested_expression_is_compiled_without_truncation()

    print("H29-C expression semantics: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
