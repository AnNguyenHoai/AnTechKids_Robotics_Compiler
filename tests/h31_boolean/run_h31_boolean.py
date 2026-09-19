#!/usr/bin/env python3
"""EPIC H31 — Boolean Expression Completeness acceptance gate.

This suite validates compiler lowering and resolved control flow without adding a
new VM/ISA dependency.  The small executor below intentionally mirrors the
existing VM truthiness contract for the opcodes relevant to boolean lowering:
zero is false and non-zero is true.
"""

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


MAX_STEPS = 10_000


def compile_source(source: str):
    compiler = RobotCompiler()
    program = compiler.compile_ast(ast.parse(source))
    return compiler, program


def execute_source(source: str):
    compiler, program = compile_source(source)
    variables = [0] * 512
    pc = 0
    steps = 0

    while pc < len(program.instructions):
        steps += 1
        if steps > MAX_STEPS:
            raise AssertionError("H31 executor exceeded step budget")

        ins = program.instructions[pc]
        opcode = Opcode(ins.opcode)

        if opcode == Opcode.LoadConst:
            value = int(ins.p2) if isinstance(ins.p2, bool) else ins.p2
            variables[ins.p1] = value
            pc += 1
        elif opcode == Opcode.Store:
            variables[ins.p2] = variables[ins.p1]
            pc += 1
        elif opcode == Opcode.CompareEQ:
            variables[ins.p3] = int(variables[ins.p1] == variables[ins.p2])
            pc += 1
        elif opcode == Opcode.CompareNE:
            variables[ins.p3] = int(variables[ins.p1] != variables[ins.p2])
            pc += 1
        elif opcode == Opcode.CompareLT:
            variables[ins.p3] = int(variables[ins.p1] < variables[ins.p2])
            pc += 1
        elif opcode == Opcode.CompareLE:
            variables[ins.p3] = int(variables[ins.p1] <= variables[ins.p2])
            pc += 1
        elif opcode == Opcode.CompareGT:
            variables[ins.p3] = int(variables[ins.p1] > variables[ins.p2])
            pc += 1
        elif opcode == Opcode.CompareGE:
            variables[ins.p3] = int(variables[ins.p1] >= variables[ins.p2])
            pc += 1
        elif opcode == Opcode.Add:
            variables[ins.p3] = variables[ins.p1] + variables[ins.p2]
            pc += 1
        elif opcode == Opcode.Sub:
            variables[ins.p3] = variables[ins.p1] - variables[ins.p2]
            pc += 1
        elif opcode == Opcode.Mul:
            variables[ins.p3] = variables[ins.p1] * variables[ins.p2]
            pc += 1
        elif opcode == Opcode.Div:
            divisor = variables[ins.p2]
            if divisor == 0:
                raise AssertionError("division by zero operand was executed")
            variables[ins.p3] = int(variables[ins.p1] / divisor)
            pc += 1
        elif opcode == Opcode.Mod:
            divisor = variables[ins.p2]
            if divisor == 0:
                raise AssertionError("modulo by zero operand was executed")
            variables[ins.p3] = variables[ins.p1] % divisor
            pc += 1
        elif opcode == Opcode.Pow:
            variables[ins.p3] = variables[ins.p1] ** variables[ins.p2]
            pc += 1
        elif opcode == Opcode.Neg:
            variables[ins.p3] = -variables[ins.p1]
            pc += 1
        elif opcode == Opcode.Jump:
            pc = ins.p2
        elif opcode == Opcode.JumpIfFalse:
            pc = ins.p2 if variables[ins.p1] == 0 else pc + 1
        elif opcode == Opcode.JumpIfTrue:
            pc = ins.p2 if variables[ins.p1] != 0 else pc + 1
        else:
            raise AssertionError(f"Unexpected opcode in H31 executor: {opcode.name}")

    return compiler, program, variables


def result_value(source: str, variable: str = "result"):
    compiler, _program, variables = execute_source(source)
    index = compiler.global_scope.resolve(variable)
    return variables[index]


def expect_value(name: str, source: str, expected, variable: str = "result"):
    actual = result_value(source, variable)
    assert actual == expected, f"{name}: expected {expected}, got {actual}"
    print(f"PASS: {name}")


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


def test_and_truth_table():
    cases = [
        (0, 0, 0),
        (0, 5, 0),
        (7, 0, 0),
        (7, -3, 1),
    ]
    for left, right, expected in cases:
        expect_value(
            f"and truth table {left!r}, {right!r}",
            f"a = {left}\nb = {right}\nresult = a and b\n",
            expected,
        )


def test_or_truth_table():
    cases = [
        (0, 0, 0),
        (0, 5, 1),
        (7, 0, 1),
        (7, -3, 1),
    ]
    for left, right, expected in cases:
        expect_value(
            f"or truth table {left!r}, {right!r}",
            f"a = {left}\nb = {right}\nresult = a or b\n",
            expected,
        )


def test_not_truthiness():
    for value, expected in [(0, 1), (1, 0), (-5, 0), (8, 0)]:
        expect_value(
            f"not truthiness {value}",
            f"a = {value}\nresult = not a\n",
            expected,
        )


def test_boolean_results_are_normalized():
    expect_value("and result normalized to one", "result = 7 and 3\n", 1)
    expect_value("or result normalized to one", "result = 0 or -2\n", 1)
    expect_value("or false result normalized to zero", "result = 0 or 0\n", 0)
    expect_value("double not normalized", "result = not not 9\n", 1)


def test_short_circuit_runtime_semantics():
    # If the second operand executes, the H31 executor deliberately fails on
    # division by zero.  Passing therefore proves runtime branch short-circuit.
    expect_value(
        "and short-circuits false left operand",
        "result = 0 and (1 / 0)\n",
        0,
    )
    expect_value(
        "or short-circuits true left operand",
        "result = 1 or (1 / 0)\n",
        1,
    )


def test_nested_arithmetic_operands_use_expression_compiler():
    expect_value(
        "and accepts nested arithmetic operands",
        "result = (1 + 1) and (3 - 2)\n",
        1,
    )
    expect_value(
        "or accepts nested arithmetic operands",
        "result = (2 - 2) or (3 * 2)\n",
        1,
    )


def test_nested_boolean_composition():
    expect_value(
        "mixed nested boolean expression",
        """
a = 1
b = 0
c = 1
d = 0
result = (a and (b or not c)) or (not d and c)
""",
        1,
    )
    expect_value(
        "deep boolean nesting",
        """
a = 1
b = 0
c = 1
d = 0
result = not ((a and not b) and (c or (d and not a)))
""",
        0,
    )


def test_python_precedence_shape_is_preserved():
    # Python AST parses this as: (not a) or (b and c).
    expect_value(
        "not/and/or precedence",
        "a = 1\nb = 1\nc = 0\nresult = not a or b and c\n",
        0,
    )
    # Python AST parses this as: a or (b and (not c)).
    expect_value(
        "or/and/not precedence",
        "a = 0\nb = 1\nc = 0\nresult = a or b and not c\n",
        1,
    )


def test_if_context():
    expect_value(
        "nested boolean expression in if",
        """
a = 1
b = 0
flag = 0
if (a and not b) or (b and not a):
    flag = 11
else:
    flag = 22
result = flag
""",
        11,
    )


def test_while_not_context():
    expect_value(
        "not expression in while condition",
        """
i = 0
while not (i >= 3):
    i = i + 1
result = i
""",
        3,
    )


def test_boolean_expression_as_api_argument_compiles():
    _compiler, program = compile_source("forward(not 0)\n")
    names = [Opcode(ins.opcode).name for ins in program.instructions]
    assert "Forward" in names, f"expected Forward, got {names}"
    assert "JumpIfFalse" in names, f"expected not lowering, got {names}"
    print("PASS: boolean expression as API argument")


def test_or_uses_existing_canonical_jump_opcode():
    _compiler, program = compile_source("a = 0\nb = 1\nresult = a or b\n")
    names = [Opcode(ins.opcode).name for ins in program.instructions]
    assert "JumpIfTrue" in names, f"expected JumpIfTrue, got {names}"
    print("PASS: or uses existing canonical JumpIfTrue opcode")


def test_scope_boundaries_remain_explicit():
    expect_error(
        "chained comparison remains out of scope",
        "a = 1\nb = 2\nc = 3\nresult = a < b < c\n",
        "Chained comparisons are not supported",
    )
    expect_error(
        "unary plus remains out of scope",
        "a = 1\nresult = +a\n",
        "Unsupported unary operator: UAdd",
    )


def main() -> int:
    test_and_truth_table()
    test_or_truth_table()
    test_not_truthiness()
    test_boolean_results_are_normalized()
    test_short_circuit_runtime_semantics()
    test_nested_arithmetic_operands_use_expression_compiler()
    test_nested_boolean_composition()
    test_python_precedence_shape_is_preserved()
    test_if_context()
    test_while_not_context()
    test_boolean_expression_as_api_argument_compiles()
    test_or_uses_existing_canonical_jump_opcode()
    test_scope_boundaries_remain_explicit()

    print("EPIC H31 Boolean Expression Completeness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
