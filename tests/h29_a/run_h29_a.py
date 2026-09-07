#!/usr/bin/env python3
"""H29-A Compiler Semantic Hardening regression suite."""

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


def compile_source(source: str):
    return RobotCompiler().compile_ast(ast.parse(source))


def expect_error(name: str, source: str, expected: str):
    try:
        compile_source(source)
    except CompilerError as exc:
        message = str(exc)
        if expected not in message:
            raise AssertionError(
                f"{name}: expected error containing {expected!r}, got {message!r}"
            )
        return
    raise AssertionError(f"{name}: compilation unexpectedly succeeded")


def main() -> int:
    tests = [
        (
            "unknown statement API",
            "import rcu\nNotARealApi(1)\n",
            "Unknown function or Robot API: 'NotARealApi()'.",
        ),
        (
            "unknown bare function",
            "mystery()\n",
            "Unknown function or Robot API: 'mystery()'.",
        ),
        (
            "unknown expression function",
            "x = mystery()\n",
            "Unknown function or Robot API: 'mystery()'.",
        ),
        (
            "undefined variable",
            "import rcu\nset_3c_led(port, 1)\n",
            "Variable 'port' is not defined.",
        ),
        (
            "unsupported syntax",
            "x = 1\nx += 1\n",
            "Unsupported syntax node: AugAssign",
        ),
        (
            "unsupported import",
            "import math\n",
            "Unsupported import: import math",
        ),
        (
            "unsupported import from",
            "from math import sqrt\n",
            "Unsupported import: from math import ...",
        ),
        (
            "keyword arguments",
            "import rcu\nset_3c_led(port=1, state=1)\n",
            "does not support keyword arguments",
        ),
        (
            "starred arguments",
            "import rcu\nset_3c_led(*(1, 1))\n",
            "does not support starred arguments",
        ),
        (
            "top-level return",
            "return\n",
            "'return' is not supported by the RoboSim language.",
        ),
        (
            "builtin name collision",
            "def set_3c_led():\n    pass\n",
            "conflicts with a built-in Robot API",
        ),
        (
            "duplicate function",
            "def move():\n    pass\ndef move():\n    pass\n",
            "Duplicate function definition",
        ),
    ]

    for name, source, expected in tests:
        expect_error(name, source, expected)
        print(f"PASS: {name}")

    compile_source("""
import rcu
speed = 20
speed = speed + 30
set_motor_speed(50, speed)
stop()
""")
    print("PASS: valid program remains compilable")

    compile_source("""
import rcu
speed = 80
speed > 50
stop()
""")
    print("PASS: top-level comparison expression remains compilable")

    print("H29-A semantic hardening: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
