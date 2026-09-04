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
    // If line is found, exit recovery immediately
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
    constexpr int RECOVERY_BASE_SPEED = 80;

    if (elapsed < 1000) {
        // Phase 1: Gentle search - turn slowly in the last known direction
        _phase = SOFT_SEARCH;
        if (direction == DIR_LEFT) {
            left = -RECOVERY_BASE_SPEED;
            right = RECOVERY_BASE_SPEED;
        } else {
            left = RECOVERY_BASE_SPEED;
            right = -RECOVERY_BASE_SPEED;
        }
        return;
    }

    if (elapsed < 2500) {
        // Phase 2: Aggressive search - faster rotation in last known direction
        _phase = DEEP_SEARCH;
        if (direction == DIR_LEFT) {
            left = -RECOVERY_BASE_SPEED;
            right = RECOVERY_BASE_SPEED;
        } else {
            left = RECOVERY_BASE_SPEED;
            right = -RECOVERY_BASE_SPEED;
        }
        // Add a slight forward motion to help find the line if it's just ahead
        // but still maintain rotation
        if (direction == DIR_LEFT) {
            left = -RECOVERY_BASE_SPEED;
            right = RECOVERY_BASE_SPEED;
        } else {
            left = RECOVERY_BASE_SPEED;
            right = -RECOVERY_BASE_SPEED;
        }
        return;
    }

    // Phase 3: Sweep - alternate directions to cover more area
    _phase = SWEEP;
    bool reverse = ((elapsed - 2500) / 800) % 2;
    Direction sweepDir = reverse ? (direction == DIR_LEFT ? DIR_RIGHT : DIR_LEFT) : direction;
    if (sweepDir == DIR_LEFT) {
        left = -RECOVERY_BASE_SPEED;
        right = RECOVERY_BASE_SPEED;
    } else {
        left = RECOVERY_BASE_SPEED;
        right = -RECOVERY_BASE_SPEED;
    }
}