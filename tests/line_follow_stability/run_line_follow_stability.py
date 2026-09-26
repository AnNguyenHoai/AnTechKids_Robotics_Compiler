#!/usr/bin/env python3
"""Regression gate for line-follow steering direction and response latency."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINE = ROOT / "robot-platform" / "main" / "src" / "Services" / "Line"


def read(name: str) -> str:
    return (LINE / name).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_int(source: str, name: str) -> int:
    match = re.search(rf"{re.escape(name)}\s*=\s*(\d+)", source)
    if not match:
        raise AssertionError(f"missing integer constant {name}")
    return int(match.group(1))


def loss_confirmation_time(sample_times_ms: list[int], confirm_ms: int) -> int | None:
    """Model the elapsed-time loss confirmation contract in the firmware."""
    candidate_since = None
    for now in sample_times_ms:
        if candidate_since is None:
            candidate_since = now
            continue
        if now - candidate_since >= confirm_ms:
            return now
    return None


def main() -> int:
    mixer = read("MotorMixer.cpp")
    estimator = read("LineErrorEstimator.cpp")
    follower = read("LineFollower.cpp")
    state_machine = read("FollowerStateMachine.cpp")
    recovery = read("RecoveryStrategy.cpp")

    # Platform steering convention: positive/right error must make the left
    # wheel faster than the right wheel; negative/left error does the reverse.
    require("baseSpeed + delta" in mixer, "positive correction must increase left motor")
    require("baseSpeed - delta" in mixer, "positive correction must decrease right motor")

    # Keep P-only behavior to avoid the previous derivative jitter, but require
    # enough authority that speed=60 produces a meaningful wheel differential.
    require("_pid(1.2f, 0.0f, 0.0f, 0.02f)" in follower,
            "default line controller must use responsive P-only tuning")
    require("_scaleFactor(15.0f)" in follower,
            "default line mixer must preserve responsive steering authority")

    base = 60
    kp = 1.2
    scale = 15.0
    full_delta = kp * 1.0 * scale
    half_delta = kp * 0.5 * scale
    require(round(base + full_delta) - round(base - full_delta) >= 30,
            "full line error must create at least 30 points of wheel differential at speed 60")
    require(round(base + half_delta) - round(base - half_delta) >= 15,
            "half line error must still create useful steering at speed 60")

    # Three-channel perception keeps intermediate offsets instead of collapsing
    # LEFT_CENTER/RIGHT_CENTER into full errors.
    require("case LineState::LEFT_CENTER:\n            return -0.5f;" in estimator,
            "LEFT_CENTER must use a half-scale error")
    require("case LineState::CENTER_RIGHT:\n            return 0.5f;" in estimator,
            "CENTER_RIGHT must use a half-scale error")

    # Loss confirmation must be based on elapsed wall time, not a fixed number
    # of VM/controller invocations. That keeps behavior stable when the scheduler
    # cadence changes or a user inserts SetWaitForTime(0.02).
    confirm_ms = extract_int(state_machine, "kLostConfirmMs")
    require("kLostConfirmSamples" not in state_machine,
            "line loss must not depend on a fixed sample count")
    require("_lostCandidateSinceMs" in state_machine,
            "line loss candidate must track a timestamp")
    require(1 <= confirm_ms <= 20,
            "line-loss confirmation window must reject glitches without adding multi-cycle latency")
    require(loss_confirmation_time([0, 5, 9], confirm_ms) is None,
            "sub-confirmation transient must not enter recovery")
    require(loss_confirmation_time([0, 20], confirm_ms) == 20,
            "20 ms student loop must confirm sustained loss on its second sample")

    # Every confirmed recovery episode must start from its first phase rather
    # than inheriting a phase timestamp from boot/system uptime.
    require("recovering && !_wasRecovering" in follower,
            "recovery must detect FOLLOWING->LOST entry")
    require("_recovery.reset();" in follower,
            "recovery must reset at episode boundaries")

    # Recovery still begins with a bounded forward arc, but the arc must be short
    # enough that it cannot dominate line-loss response latency.
    soft_ms = extract_int(recovery, "kSoftSearchMs")
    require(soft_ms <= 150,
            "soft recovery must hand off to pivot search within 150 ms")
    require("kSoftInnerSpeed = 35" in recovery and "kSoftOuterSpeed = 65" in recovery,
            "soft recovery must remain a bounded forward arc")
    require("kDeepPivotSpeed = 45" in recovery,
            "deep recovery pivot must remain bounded")
    require("RECOVERY_BASE_SPEED = 80" not in recovery,
            "legacy immediate +/-80 recovery must not return")

    print("PASS: line-follow steering and temporal response contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
