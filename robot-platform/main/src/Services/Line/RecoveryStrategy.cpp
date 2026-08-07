#include "RecoveryStrategy.h"
#include <Arduino.h>

RecoveryStrategy::RecoveryStrategy() : _phase(SEARCH_LEFT), _speed(40) {}

void RecoveryStrategy::reset() {
    _phase = SEARCH_LEFT;
    _phaseStart = millis();
}

void RecoveryStrategy::update(uint8_t mask, int &left, int &right) {
    if (mask != 0) {
        reset();          // <-- reset phase về SEARCH_LEFT
        left = right = 0;
        return;
    }

    uint32_t now = millis();
    switch (_phase) {
        case SEARCH_LEFT:
            left = -_speed;
            right = _speed;
            if (now - _phaseStart > 300) {
                _phase = SEARCH_RIGHT;
                _phaseStart = now;
            }
            break;
        case SEARCH_RIGHT:
            left = _speed;
            right = -_speed;
            if (now - _phaseStart > 300) {
                _phase = SEARCH_SPIRAL;
                _phaseStart = now;
            }
            break;
        case SEARCH_SPIRAL: {
            int factor = (now - _phaseStart) / 100;
            if (factor > 5) factor = 5;
            left = -_speed * (1 + factor);
            right = _speed * (1 + factor);
            break;
        }
    }
}