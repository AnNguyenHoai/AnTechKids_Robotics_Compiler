"""H26-F compiler safety gate for compiled Program objects.

This module is additive: existing RobotCompiler behavior is unchanged. Tooling may
call validate_program() before handing a Program to a firmware/runtime boundary.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

_ROOT = Path(__file__).resolve().parents[2]
_RESOURCE_MANIFEST = _ROOT / "packages" / "robot-isa" / "resource_contract.json"
_CAPABILITY_MANIFEST = _ROOT / "packages" / "robot-isa" / "capability_model.json"
_ISA_MANIFEST = _ROOT / "packages" / "robot-isa" / "canonical_isa.json"


@dataclass(frozen=True)
class SafetyViolation:
    rule: str
    message: str
    instruction_index: int | None = None
    opcode: int | None = None


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_resource_contract(path: Path = _RESOURCE_MANIFEST) -> Mapping:
    return _load(path)


def load_capability_model(path: Path = _CAPABILITY_MANIFEST) -> Mapping:
    return _load(path)


def _opcode_value(instruction) -> int:
    raw = instruction.opcode if hasattr(instruction, "opcode") else instruction.get("opcode")
    return int(getattr(raw, "value", raw))


def _operand_values(instruction) -> tuple[int, ...]:
    if hasattr(instruction, "p1"):
        return (instruction.p1, instruction.p2, instruction.p3, instruction.p4)
    return tuple(instruction.get(name, 0) for name in ("p1", "p2", "p3", "p4"))


def _required_variable_indices(opcode: int, operands: Sequence[int]) -> tuple[int, ...]:
    """Return operand positions whose values are variable indices.

    The mapping intentionally follows the current production instruction semantics.
    Constants/targets are excluded so a literal value cannot be mistaken for a
    variable resource violation.
    """
    roles = {
        1: (0,), 2: (0,), 3: (0,), 4: (0,), 5: (0,), 6: (), 7: (0,),
        8: (0, 1, 2), 9: (0, 1, 2), 10: (0, 1, 2), 11: (0, 1, 2),
        12: (0, 1, 2), 13: (0, 1, 2), 20: (0, 1, 2), 21: (0, 1, 2),
        22: (0, 1, 2), 23: (0, 1, 2), 24: (0, 1, 2), 25: (0, 1, 2),
        26: (0, 2), 27: (0,), 29: (0, 1), 30: (0,), 31: (0, 1),
        32: (0, 1), 33: (0,), 34: (0, 1), 35: (0, 1), 36: (0, 1),
        37: (0, 1), 38: (0, 1), 39: (0, 1, 2, 3), 40: (0, 1),
        41: (0,), 42: (0, 1, 2), 43: (0, 1, 2), 44: (0, 2), 47: (0,),
        48: (0,), 49: (), 50: (0, 1, 2), 51: (0, 1), 52: (), 53: (),
        54: (0,), 55: (0, 1), 56: (0, 1), 57: (0, 1), 58: (0, 1),
        59: (0, 1), 60: (), 61: (0,), 62: (0,), 63: (0,), 64: (),
    }
    return tuple(operands[i] for i in roles.get(opcode, ()) if i < len(operands))


def validate_instructions(
    instructions: Iterable,
    *,
    target_capabilities: Iterable[str] | None = None,
    resource_contract: Mapping | None = None,
    capability_model: Mapping | None = None,
    isa_manifest: Mapping | None = None,
) -> tuple[SafetyViolation, ...]:
    """Validate a compiled instruction sequence without changing it."""
    resources = resource_contract or load_resource_contract()
    capabilities = capability_model or load_capability_model()
    isa = isa_manifest or _load(_ISA_MANIFEST)
    rows = isa["rows"]
    known_codes = {int(row[2]) for row in rows}
    capability_by_opcode: dict[int, set[str]] = {}
    for cap in capabilities["capabilities"]:
        for code in cap["opcodes"]:
            capability_by_opcode.setdefault(int(code), set()).add(cap["id"])
    allowed_caps = set(target_capabilities) if target_capabilities is not None else None

    items = tuple(instructions)
    max_instructions = int(resources["program"]["max_instructions"])
    max_variables = int(resources["runtime"]["max_variables"])
    max_call_stack = int(resources["runtime"]["max_call_stack"])
    operand_min = int(resources["operands"]["min"])
    operand_max = int(resources["operands"]["max"])
    allow_end = bool(resources["jump_targets"]["allow_end"])

    violations: list[SafetyViolation] = []
    if len(items) > max_instructions:
        violations.append(SafetyViolation("program_overflow", f"Program has {len(items)} instructions; maximum is {max_instructions}."))

    call_depth = 0
    max_depth = 0
    for index, instruction in enumerate(items):
        opcode = _opcode_value(instruction)
        operands = _operand_values(instruction)
        if opcode not in known_codes:
            violations.append(SafetyViolation("invalid_opcode", f"Unknown opcode {opcode}.", index, opcode))
            continue

        if allowed_caps is not None:
            missing = capability_by_opcode.get(opcode, set()) - allowed_caps
            if missing:
                required = ", ".join(sorted(missing))
                violations.append(SafetyViolation("unsupported_capability", f"Opcode {opcode} requires unsupported capability set: {required}.", index, opcode))

        for value in operands:
            if not operand_min <= int(value) <= operand_max:
                violations.append(SafetyViolation("invalid_operand", f"Operand {value} is outside int32 range.", index, opcode))
                break

        variable_indices = _required_variable_indices(opcode, operands)
        for value in variable_indices:
            if not 0 <= int(value) < max_variables:
                violations.append(SafetyViolation("invalid_variable", f"Variable index {value} is outside 0..{max_variables - 1}.", index, opcode))
                break

        if opcode in (14, 15, 16):
            target = int(operands[1])
            upper = len(items) if allow_end else len(items) - 1
            if target < 0 or target > upper:
                violations.append(SafetyViolation("invalid_jump", f"Jump target {target} is outside valid range 0..{upper}.", index, opcode))

        if opcode == 27:
            call_depth += 1
            max_depth = max(max_depth, call_depth)
            if max_depth > max_call_stack:
                violations.append(SafetyViolation("stack_overflow", f"Static call depth exceeds maximum stack depth {max_call_stack}.", index, opcode))
                break
        elif opcode == 28:
            call_depth -= 1
            if call_depth < 0:
                violations.append(SafetyViolation("invalid_return", "Return appears without a preceding call in the linear flow.", index, opcode))
                call_depth = 0

    return tuple(violations)


def validate_program(program, **kwargs) -> tuple[SafetyViolation, ...]:
    return validate_instructions(program.instructions, **kwargs)


def assert_safe(program, **kwargs) -> None:
    violations = validate_program(program, **kwargs)
    if violations:
        detail = "\n".join(
            f"[{v.rule}]" + (f" instruction {v.instruction_index}" if v.instruction_index is not None else "") + f": {v.message}"
            for v in violations
        )
        raise ValueError(detail)
