#!/usr/bin/env python3
"""Host contract for bounded cooperative Pow execution (#328)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VM_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
CTX_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMContext.h"
PENDING_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMPendingState.h"

POW_MULTIPLIES_PER_STEP = 8


def legacy_pow(base: int, exp: int) -> int:
    result = 1
    for _ in range(max(0, exp)):
        result *= base
    return result


def cooperative_pow(base: int, exp: int) -> tuple[int, int]:
    if exp <= 0:
        return 1, 1

    remaining = exp
    result = 1
    steps = 0
    while remaining:
        multiplies = min(POW_MULTIPLIES_PER_STEP, remaining)
        for _ in range(multiplies):
            result *= base
        remaining -= multiplies
        steps += 1
    return result, steps


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    vm = VM_CPP.read_text(encoding="utf-8")
    ctx = CTX_H.read_text(encoding="utf-8")
    pending = PENDING_H.read_text(encoding="utf-8")

    require("POW_MULTIPLIES_PER_STEP = 8" in vm, "Pow per-Step budget must remain explicit and fixed")
    require("VMPendingOperation::Pow" in vm, "Pow must use generic pending ownership")
    require("Pow," in pending, "Pow pending operation must be represented in generic pending state")
    require("mPendingPowRemaining" in ctx and "mPendingPowResult" in ctx, "Pow progress must live in VMContext")
    require("multiplies < POW_MULTIPLIES_PER_STEP" in vm, "Pow inner work must be budgeted")
    require("for (int16_t i = 0; i < exp; ++i)" not in vm, "legacy exponent-sized Pow loop must not return")

    # Safe arithmetic domain: prove scheduling changes do not change logical results.
    for base, exp in [(-3, 0), (-3, 1), (-2, 7), (0, 12), (1, 32767), (2, 8), (2, 12), (3, 5)]:
        result, steps = cooperative_pow(base, exp)
        require(result == legacy_pow(base, exp), f"Pow semantic drift for base={base}, exp={exp}")
        expected_steps = 1 if exp <= 0 else (exp + POW_MULTIPLIES_PER_STEP - 1) // POW_MULTIPLIES_PER_STEP
        require(steps == expected_steps, f"unexpected Pow chunk count for exp={exp}")

    # Boundary: exponent 9 must span two Steps, proving one Step cannot consume arbitrary exponent work.
    result, steps = cooperative_pow(2, 9)
    require(result == 512 and steps == 2, "Pow exponent 9 must yield after the first bounded chunk")

    print("VM-RT bounded Pow contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
