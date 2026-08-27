#include "RecoveryStrategy.h"
#include <Arduino.h>

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
    // A visible line must immediately leave recovery.  Do not output one more
    // search command after reacquisition.
    if (mask != 0) {
        reset();
        left = right = 0;
        return;
    }

    uint32_t now = millis();
    uint32_t elapsed = now - _phaseStart;
    Direction direction = _lastDirection == DIR_UNKNOWN ? DIR_LEFT : _lastDirection;

    // H22: recovery commands stay in the normal command domain. Calibration is
    // applied once later by RobotAPI. Avoid low commands that can hum/stall after
    // motor scaling.
    constexpr int RECOVERY_BASE_SPEED = 100;
    constexpr int RECOVERY_SOFT_DELTA = 12;
    constexpr int RECOVERY_DEEP_DELTA = 22;

    if (elapsed < 700) {
        _phase = SOFT_SEARCH;
        if (direction == DIR_LEFT) { left = RECOVERY_BASE_SPEED - RECOVERY_SOFT_DELTA; right = RECOVERY_BASE_SPEED; }
        else                       { left = RECOVERY_BASE_SPEED; right = RECOVERY_BASE_SPEED - RECOVERY_SOFT_DELTA; }
        return;
    }

    if (elapsed < 1800) {
        _phase = DEEP_SEARCH;
        if (direction == DIR_LEFT) { left = RECOVERY_BASE_SPEED - RECOVERY_DEEP_DELTA; right = RECOVERY_BASE_SPEED; }
        else                       { left = RECOVERY_BASE_SPEED; right = RECOVERY_BASE_SPEED - RECOVERY_DEEP_DELTA; }
        return;
    }

    _phase = SWEEP;
    // Slow alternating sweep.  Direction changes only after sustained loss.
    bool reverse = ((elapsed - 1800) / 800) % 2;
    Direction sweepDir = reverse ? (direction == DIR_LEFT ? DIR_RIGHT : DIR_LEFT) : direction;
    if (sweepDir == DIR_LEFT) { left = -70; right = 70; }
    else                      { left = 70; right = -70; }
}
