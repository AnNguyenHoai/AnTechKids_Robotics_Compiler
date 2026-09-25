#!/usr/bin/env python3
"""Host contract for deadline-owned VM pending operations (#331)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CTX = ROOT / "robot-platform/main/src/Services/VM/VMContext.h"
VM = ROOT / "robot-platform/main/src/Services/VM/VM.cpp"

UINT32_MASK = 0xFFFFFFFF


def signed32(value: int) -> int:
    value &= UINT32_MASK
    return value - 0x100000000 if value & 0x80000000 else value


def deadline_reached(now_ms: int, deadline_ms: int) -> bool:
    return signed32((now_ms - deadline_ms) & UINT32_MASK) >= 0


def main() -> int:
    ctx = CTX.read_text(encoding="utf-8")
    vm = VM.read_text(encoding="utf-8")

    start = ctx.index("bool IsPendingDeadlineReached")
    end = ctx.index("public:", start)
    helper = ctx[start:end]

    assert "mPendingOperation.IsPending()" in helper
    assert "mPendingOperation.IsOwnedBy(mProgramCounter)" in helper
    assert "VMPendingOperation::Wait" in helper
    assert "VMPendingOperation::Mp3Play" in helper
    assert "static_cast<int32_t>(nowMs - mPendingDeadlineMs) >= 0" in helper

    mp3_start = vm.index("case Opcode::SetMp3Play:")
    mp3_end = vm.index("case Opcode::GetTraceValue:", mp3_start)
    mp3 = vm[mp3_start:mp3_end]
    assert "mContext.mPendingOperation = VMPendingOperation::Mp3Play;" in mp3
    assert "mContext.mPendingDeadlineMs = millis() + durationMs;" in mp3
    assert "mContext.IsPendingDeadlineReached(millis())" in mp3
    assert mp3.index("RobotAPI::EndMp3PlayCooperative();") < mp3.index("mContext.ClearPendingOperation();")
    assert mp3.index("mContext.ClearPendingOperation();") < mp3.rindex("mContext.mProgramCounter++;")

    # Normal deadline behavior.
    assert not deadline_reached(99, 100)
    assert deadline_reached(100, 100)
    assert deadline_reached(101, 100)

    # millis() wrap-around behavior: deadline just after wrap is still ordered
    # correctly by signed subtraction within the supported half-range window.
    deadline = 0x00000005
    assert not deadline_reached(0xFFFFFFFE, deadline)
    assert deadline_reached(0x00000005, deadline)
    assert deadline_reached(0x00000006, deadline)

    print("VM pending deadline contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
