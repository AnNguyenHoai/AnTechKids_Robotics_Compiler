#include "FollowerStateMachine.h"
#include <Arduino.h>

namespace {
constexpr uint32_t LINE_LOST_DEBOUNCE_MS = 40;
constexpr uint32_t DEEP_SEARCH_AFTER_MS = 500;
}

FollowerStateMachine::FollowerStateMachine()
    : _state(FollowerState::FOLLOWING),
      _turnRequested(false),
      _turnDirection(0),
      _stopRequested(false),
      _lostTimer(0),
      _zeroMaskSince(0),
      _zeroMaskPending(false),
      _searchingDirection(0) {}

void FollowerStateMachine::update(uint8_t mask, bool intersectionDetected, bool turnRequested, bool stopRequested) {
    _turnRequested = turnRequested;
    _stopRequested = stopRequested;

    switch (_state) {
        case FollowerState::FOLLOWING:
            if (intersectionDetected && _stopRequested) {
                _zeroMaskPending = false;
                transitionTo(FollowerState::INTERSECTION);
            } else if (mask == 0) {
                const uint32_t now = millis();
                if (!_zeroMaskPending) {
                    _zeroMaskPending = true;
                    _zeroMaskSince = now;
                } else if ((uint32_t)(now - _zeroMaskSince) >= LINE_LOST_DEBOUNCE_MS) {
                    _zeroMaskPending = false;
                    _lostTimer = now;
                    transitionTo(FollowerState::LOST);
                }
            } else {
                // A short 00000 gap is treated as sensor dropout, not a real
                // line-loss event. Clear the debounce as soon as any eye sees line.
                _zeroMaskPending = false;
                _zeroMaskSince = 0;
                if (_turnRequested) {
                    transitionTo(FollowerState::TURNING);
                    // direction already stored via requestTurn()
                }
            }
            break;

        case FollowerState::LOST:
            if (mask != 0) {
                transitionTo(FollowerState::FOLLOWING);
            } else if ((uint32_t)(millis() - _lostTimer) > DEEP_SEARCH_AFTER_MS) {
                transitionTo(FollowerState::SEARCHING);
                _searchingDirection = 0; // start left
            }
            break;

        case FollowerState::SEARCHING:
            if (mask != 0) {
                transitionTo(FollowerState::FOLLOWING);
            }
            break;

        case FollowerState::INTERSECTION:
            if (!_stopRequested) {
                transitionTo(FollowerState::FOLLOWING);
            }
            break;

        case FollowerState::TURNING:
            if (mask != 0) {
                transitionTo(FollowerState::FOLLOWING);
                _turnRequested = false;
            }
            break;
    }
}

MotionIntent FollowerStateMachine::getMotionIntent() const {
    switch (_state) {
        case FollowerState::FOLLOWING:
            return MotionIntent::FOLLOW;
        case FollowerState::LOST:
        case FollowerState::SEARCHING:
            return MotionIntent::RECOVER;
        case FollowerState::INTERSECTION:
            return MotionIntent::STOP;
        case FollowerState::TURNING:
            return (_turnDirection == 1) ? MotionIntent::TURN_LEFT : MotionIntent::TURN_RIGHT;
        default:
            return MotionIntent::STOP;
    }
}

void FollowerStateMachine::requestTurn(int direction) {
    _turnRequested = true;
    _turnDirection = direction;
}

void FollowerStateMachine::requestStopAtIntersection() {
    _stopRequested = true;
}

void FollowerStateMachine::reset() {
    _state = FollowerState::FOLLOWING;
    _turnRequested = false;
    _stopRequested = false;
    _lostTimer = 0;
    _zeroMaskSince = 0;
    _zeroMaskPending = false;
    _searchingDirection = 0;
}

void FollowerStateMachine::transitionTo(FollowerState newState) {
    _state = newState;
}