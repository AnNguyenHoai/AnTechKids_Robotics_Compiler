#!/usr/bin/env python3
"""VM-RT blocking compatibility API boundary contract (#338).

Public RobotAPI blocking helpers may remain for non-VM compatibility, but VM
opcode dispatch must never call them directly. Cooperative VM paths own the
corresponding bytecode behavior.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VM_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"

FORBIDDEN_VM_CALLS = (
    "RobotAPI::Wait(",
    "RobotAPI::LineMillisecond(",
    "RobotAPI::LineIntersectionStop(",
    "RobotAPI::LineTurnEncounterLine(",
    "RobotAPI::LineForBmp(",
)


def validate_vm_source(source: str) -> list[str]:
    errors: list[str] = []
    for call in FORBIDDEN_VM_CALLS:
        if call in source:
            errors.append(f"VM dispatch must not call blocking compatibility API: {call}")
    return errors


def main() -> int:
    source = VM_CPP.read_text(encoding="utf-8")
    errors = validate_vm_source(source)
    if errors:
        raise AssertionError("VM blocking API boundary violation(s):\n- " + "\n- ".join(errors))

    # Fail-closed mutation proof: every forbidden compatibility call must be
    # independently rejected if it is reintroduced into VM.cpp.
    insertion = source.find("void VM::Step()")
    if insertion < 0:
        raise AssertionError("VM::Step boundary unavailable for mutation proof")

    for call in FORBIDDEN_VM_CALLS:
        mutated = source[:insertion] + f"// mutation\nvoid vm_rt_forbidden_probe() {{ {call}0); }}\n" + source[insertion:]
        mutation_errors = validate_vm_source(mutated)
        if not any(call in error for error in mutation_errors):
            raise AssertionError(f"mutation unexpectedly passed for {call}")
        print(f"PASS: rejected {call}")

    print("VM-RT blocking compatibility API boundary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
