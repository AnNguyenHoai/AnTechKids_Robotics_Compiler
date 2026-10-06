from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINE = ROOT / "robot-platform/main/src/Services/Line"
ROBOT_API = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"

HARNESS = r"""
#include <cassert>
#include <cmath>
#include <cstdint>
#include "LineErrorEstimator.h"
#include "LinePerception.h"
#include "IntersectionDetector.h"
#include "RecoveryStrategy.h"

static uint32_t g_now = 0;
uint32_t millis() { return g_now; }

static void assert_close(float a, float b) {
    assert(std::fabs(a - b) < 0.0001f);
}

int main() {
    struct PerceptionCase {
        uint8_t mask;
        float error;
        LineState state;
    };

    const PerceptionCase cases[] = {
        {0b00100,  0.0f, LineState::CENTER},
        {0b01100, -0.5f, LineState::LEFT_CENTER},
        {0b11000, -1.5f, LineState::LEFT},
        {0b00011,  1.5f, LineState::RIGHT},
        {0b00000,  0.0f, LineState::LOST},
        {0b11111,  0.0f, LineState::INTERSECTION},
    };

    for (const auto& c : cases) {
        assert_close(LineErrorEstimator::estimate(c.mask), c.error);
        assert(LinePerception::interpret(c.mask) == c.state);
    }

    // Extra center-right representative point.
    assert_close(LineErrorEstimator::estimate(0b00110), 0.5f);
    assert(LinePerception::interpret(0b00110) == LineState::CENTER_RIGHT);

    // High bits must not leak into the five-bit contract.
    assert_close(LineErrorEstimator::estimate(0b11100100), 0.0f);
    assert(LinePerception::interpret(0b11100100) == LineState::CENTER);

    // Intersection temporal policy currently requires 3..5 candidate samples
    // in the six-sample history. This test intentionally records current V1
    // behavior; hardware validation may change it later.
    {
        IntersectionDetector detector;
        for (int i = 0; i < 5; ++i) {
            assert(!detector.update(0b11111));
        }
        assert(!detector.update(0b00100)); // history now has five candidates
        assert(detector.update(0b11111));  // still five candidates after rollover
    }

    {
        IntersectionDetector detector;
        for (int i = 0; i < 6; ++i) {
            assert(!detector.update(0b11111));
        }
    }

    // Recovery follows the last meaningful side; no hardware timing tuning is
    // encoded here beyond the frozen V1 phase boundaries.
    {
        g_now = 100;
        RecoveryStrategy recovery;
        recovery.setLastDirection(RecoveryStrategy::DIR_RIGHT);
        recovery.reset();

        int left = 0, right = 0;
        recovery.update(0, left, right);
        assert(left == 80 && right == -80);

        g_now = 1200;
        recovery.update(0, left, right);
        assert(left == 80 && right == -80);

        // Reacquire exits recovery immediately and commands zero from strategy.
        recovery.update(0b00100, left, right);
        assert(left == 0 && right == 0);
    }

    return 0;
}
"""

ARDUINO_STUB = r"""
#pragma once
#include <stdint.h>
uint32_t millis();
"""

def test_real_cpp_perception_control_components() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        stub = td / "Arduino.h"
        src = td / "line_perception_test.cpp"
        exe = td / "line_perception_test"
        stub.write_text(ARDUINO_STUB, encoding="utf-8")
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(td),
            "-I", str(LINE),
            str(src),
            str(LINE / "LineErrorEstimator.cpp"),
            str(LINE / "LinePerception.cpp"),
            str(LINE / "IntersectionDetector.cpp"),
            str(LINE / "RecoveryStrategy.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_line_follower_wiring_and_diagnostics_preserved() -> None:
    follower = (LINE / "LineFollower.cpp").read_text(encoding="utf-8")
    api = ROBOT_API.read_text(encoding="utf-8")

    assert "LineErrorEstimator::estimate(mask)" in follower
    assert "LAST_DIRECTION_THRESHOLD = 0.25f" in follower
    assert "_intersectionDetector.update(mask)" in follower
    assert "_recovery.update(mask, leftMotor, rightMotor)" in follower
    assert "_pid.reset()" in follower

    assert "g_lineResponseDiagnosticEnabled" in api
    assert "sensorStartUs" in api
    assert "sensorDoneUs" in api
    assert "controlDoneUs" in api
    assert "outputDoneUs" in api
    assert "[LINE-RESPONSE]" in api


def test_no_unverified_station_algorithm_was_invented() -> None:
    # V2-SW-006 preserves the frozen V1 algorithm. There is no distinct station
    # classifier in the baseline; do not silently add one without a requirement
    # and hardware evidence.
    names = [p.name.lower() for p in LINE.glob("*")]
    assert not any("station" in name for name in names)


def main() -> int:
    test_real_cpp_perception_control_components()
    print("PASS: real C++ Line5 estimator/perception/intersection/recovery regression")
    test_line_follower_wiring_and_diagnostics_preserved()
    print("PASS: LineFollower component wiring and line-response diagnostics preserved")
    test_no_unverified_station_algorithm_was_invented()
    print("PASS: no unsupported station-pattern algorithm invented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
