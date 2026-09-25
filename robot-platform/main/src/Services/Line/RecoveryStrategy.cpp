#include "RecoveryStrategy.h"
#include <Arduino.h>

namespace {
// Keep a short forward arc to avoid the old immediate +/-80 snap, but do not
// spend 300 ms driving away from the last observed line before pivot recovery.
constexpr uint32_t kSoftSearchMs = 120;
constexpr uint32_t kDeepSearchMs = 1200;
constexpr uint32_t kSweepPeriodMs = 700;
constexpr int kSoftInnerSpeed = 35;
constexpr int kSoftOuterSpeed = 65;
constexpr int kDeepPivotSpeed = 45;
constexpr int kSweepPivotSpeed = 55;
}

RecoveryStrategy::RecoveryStrategy()
    : _phase(SOFT_SEARCH), _phaseStart(0), _lastDirection(DIR_UNKNOWN) {}

void RecoveryStrategy::reset() {
    _phase = SOFT_SEARCH;
    _phaseStart = millis();
}

void RecoveryStrategy::setLastDirection(Direction direction) {
    if (direction != DIR_UNKNOWN) {
        _lastDirection = direction;
    }
}

void RecoveryStrategy::update(uint8_t mask, int &left, int &right) {
    // If line is found, exit recovery immediately.
    if (mask != 0) {
        reset();
        left = right = 0;
        return;
    }

    const uint32_t now = millis();
    const uint32_t elapsed = now - _phaseStart;
    const Direction direction = _lastDirection == DIR_UNKNOWN ? DIR_LEFT : _lastDirection;

    if (elapsed < kSoftSearchMs) {
        // First response to a confirmed loss is a forward arc, not a pivot.
        // This keeps momentum while steering toward the last observed side.
        _phase = SOFT_SEARCH;
        if (direction == DIR_LEFT) {
            left = kSoftInnerSpeed;
            right = kSoftOuterSpeed;
        } else {
            left = kSoftOuterSpeed;
            right = kSoftInnerSpeed;
        }
        return;
    }

    if (elapsed < kDeepSearchMs) {
        // Pivot promptly once the short soft arc failed to reacquire the line.
        _phase = DEEP_SEARCH;
        if (direction == DIR_LEFT) {
            left = -kDeepPivotSpeed;
            right = kDeepPivotSpeed;
        } else {
            left = kDeepPivotSpeed;
            right = -kDeepPivotSpeed;
        }
        return;
    }

    // Long loss: sweep around the last known direction with a bounded pivot.
    _phase = SWEEP;
    const bool reverse = ((elapsed - kDeepSearchMs) / kSweepPeriodMs) % 2;
    const Direction sweepDir = reverse
        ? (direction == DIR_LEFT ? DIR_RIGHT : DIR_LEFT)
        : direction;
    if (sweepDir == DIR_LEFT) {
        left = -kSweepPivotSpeed;
        right = kSweepPivotSpeed;
    } else {
        left = kSweepPivotSpeed;
        right = -kSweepPivotSpeed;
    }
}
