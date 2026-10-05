from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
sys.path.insert(0, str(COMPILER_ROOT))

from compiler.compiler import RobotCompiler
from compiler.error import CompilerError, syntax_error_diagnostic


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def expect_compile_error(source, expected_message):
    try:
        RobotCompiler().compile_ast(ast.parse(source))
    except CompilerError as exc:
        check(expected_message in str(exc), f"compiler reports {expected_message!r}")
        diagnostic = exc.to_diagnostic()
        check(diagnostic["code"] == "E_COMPILE", "compiler error keeps stable E_COMPILE code")
        check(diagnostic["context"].get("line") == 2, "compiler diagnostic reports source line")
        check(diagnostic["context"].get("column") == 1, "compiler diagnostic reports 1-based source column")
        check(bool(diagnostic["context"].get("syntax_node")), "compiler diagnostic reports AST node type")
        check(bool(diagnostic["context"].get("hint")), "compiler diagnostic includes actionable hint")
        return
    raise AssertionError("CompilerError expected")


expect_compile_error("x = 1\nunknown_robot_api()\n", "Unknown function or Robot API")

try:
    ast.parse("x = 1\nif x >:\n    x = 2\n")
except SyntaxError as exc:
    diagnostic = syntax_error_diagnostic(exc)
    check(diagnostic["code"] == "INVALID_SOURCE", "syntax error has stable INVALID_SOURCE code")
    check(diagnostic["context"].get("line") == 2, "syntax diagnostic reports parser line")
    check(isinstance(diagnostic["context"].get("column"), int), "syntax diagnostic reports parser column")
    check("if x >:" in diagnostic["context"].get("source", ""), "syntax diagnostic includes source text")
    check(bool(diagnostic["context"].get("hint")), "syntax diagnostic includes actionable hint")
else:
    raise AssertionError("SyntaxError expected")

print("H37 compiler diagnostics regression: PASS")
