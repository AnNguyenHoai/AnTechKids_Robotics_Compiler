"""Opt-in safe compilation wrapper.

The legacy RobotCompiler entry point is intentionally untouched. Call compile_safe()
when a tool or IDE wants the H26-F safety gate before runtime delivery.
"""
from __future__ import annotations

from .compiler import RobotCompiler
from .safety_validator import validate_program


def compile_safe(filename: str, *, target_capabilities=None):
    compiler = RobotCompiler()
    program = compiler.compile(filename)
    violations = validate_program(program, target_capabilities=target_capabilities)
    if violations:
        detail = "\n".join(f"[{v.rule}] {v.message}" for v in violations)
        raise ValueError(f"Compiler safety validation failed:\n{detail}")
    return program
