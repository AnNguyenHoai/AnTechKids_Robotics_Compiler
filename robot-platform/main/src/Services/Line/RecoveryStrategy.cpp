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
    if (mask != 0) {
        reset();
        left = right = 0;
        return;
    }

    const uint32_t now = millis();
    const uint32_t elapsed = now - _phaseStart;
    const Direction direction = _lastDirection == DIR_UNKNOWN ? DIR_LEFT : _lastDirection;

    // Recovery is intentionally progressive. A freshly confirmed line loss
    // first uses a forward arc so neither motor reverses abruptly. Only a
    // persistent loss escalates to in-place search.
    constexpr int SOFT_INNER_SPEED = 25;
    constexpr int SOFT_OUTER_SPEED = 65;
    constexpr int DEEP_SEARCH_SPEED = 45;
    constexpr int SWEEP_SPEED = 60;
    constexpr uint32_t SOFT_SEARCH_MS = 300;
    constexpr uint32_t DEEP_SEARCH_MS = 1200;

    if (elapsed < SOFT_SEARCH_MS) {
        _phase = SOFT_SEARCH;
        if (direction == DIR_LEFT) {
            left = SOFT_INNER_SPEED;
            right = SOFT_OUTER_SPEED;
        } else {
            left = SOFT_OUTER_SPEED;
            right = SOFT_INNER_SPEED;
        }
        return;
    }

    if (elapsed < DEEP_SEARCH_MS) {
        _phase = DEEP_SEARCH;
        if (direction == DIR_LEFT) {
            left = -DEEP_SEARCH_SPEED;
            right = DEEP_SEARCH_SPEED;
        } else {
            left = DEEP_SEARCH_SPEED;
            right = -DEEP_SEARCH_SPEED;
        }
        return;
    }

    _phase = SWEEP;
    const bool reverse = ((elapsed - DEEP_SEARCH_MS) / 700) % 2;
    const Direction sweepDir =
        reverse ? (direction == DIR_LEFT ? DIR_RIGHT : DIR_LEFT) : direction;

    if (sweepDir == DIR_LEFT) {
        left = -SWEEP_SPEED;
        right = SWEEP_SPEED;
    } else {
        left = SWEEP_SPEED;
        right = -SWEEP_SPEED;
    }
}
