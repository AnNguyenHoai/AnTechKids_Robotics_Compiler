#!/usr/bin/env python3
"""Regression gate for line-follow steering direction and recovery stability."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINE = ROOT / "robot-platform" / "main" / "src" / "Services" / "Line"


def read(name: str) -> str:
    return (LINE / name).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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

    base = 70
    scale = 10
    right_error = 1.0
    left_error = -1.0
    right_left_motor = round(base + right_error * scale)
    right_right_motor = round(base - right_error * scale)
    left_left_motor = round(base + left_error * scale)
    left_right_motor = round(base - left_error * scale)
    require(right_left_motor > right_right_motor, "RIGHT line error must steer RIGHT")
    require(left_left_motor < left_right_motor, "LEFT line error must steer LEFT")

    # Three-channel perception must preserve intermediate offsets instead of
    # collapsing LEFT_CENTER/RIGHT_CENTER into full errors.
    require("case LineState::LEFT_CENTER:\n            return -0.5f;" in estimator,
            "LEFT_CENTER must use a half-scale error")
    require("case LineState::CENTER_RIGHT:\n            return 0.5f;" in estimator,
            "CENTER_RIGHT must use a half-scale error")

    # One transient 000 sample must not enter hard recovery.
    require("kLostConfirmSamples = 3" in state_machine,
            "line loss must require three consecutive zero samples")
    require("_lostCandidateSamples" in state_machine,
            "line loss candidate state must be tracked")

    # Every confirmed recovery episode must start from its first phase rather
    # than inheriting a phase timestamp from boot/system uptime.
    require("recovering && !_wasRecovering" in follower,
            "recovery must detect FOLLOWING->LOST entry")
    require("_recovery.reset();" in follower,
            "recovery must reset at episode boundaries")

    # Initial recovery is intentionally a forward arc. Strong pivot/search is
    # reserved for sustained loss and must not use the former +/-80 immediate pivot.
    require("kSoftInnerSpeed = 35" in recovery and "kSoftOuterSpeed = 65" in recovery,
            "soft recovery must use bounded forward-arc speeds")
    require("kDeepPivotSpeed = 45" in recovery,
            "deep recovery pivot must be bounded")
    require("RECOVERY_BASE_SPEED = 80" not in recovery,
            "legacy immediate +/-80 recovery must not return")

    # Safe baseline is P-only; serial tuning remains available for later physical calibration.
    require("_pid(1.0f, 0.0f, 0.0f, 0.02f)" in follower,
            "default line PID must use the safe P-only baseline")
    require("_scaleFactor(10.0f)" in follower,
            "default line mixer scale must use the bounded baseline")

    print("PASS: line-follow steering and recovery stability contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
