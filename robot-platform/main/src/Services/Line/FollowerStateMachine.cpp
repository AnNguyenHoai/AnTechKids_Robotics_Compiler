#include "FollowerStateMachine.h"
#include <Arduino.h>

namespace {
// Confirm a real line loss by elapsed time instead of by scheduler-dependent
// sample count. With a 20 ms user wait this confirms on the second lost sample;
// with a faster loop it still rejects sub-10 ms transients.
constexpr uint32_t kLostConfirmMs = 10;
}

FollowerStateMachine::FollowerStateMachine()
    : _state(FollowerState::FOLLOWING),
      _turnRequested(false),
      _turnDirection(0),
      _stopRequested(false),
      _lostTimer(0),
      _searchingDirection(0),
      _lostCandidateActive(false),
      _lostCandidateSinceMs(0) {}

void FollowerStateMachine::clearLostCandidate() {
    _lostCandidateActive = false;
    _lostCandidateSinceMs = 0;
}

void FollowerStateMachine::update(uint8_t mask, bool intersectionDetected, bool turnRequested, bool stopRequested) {
    _turnRequested = turnRequested;
    _stopRequested = stopRequested;

    switch (_state) {
        case FollowerState::FOLLOWING:
            if (intersectionDetected && _stopRequested) {
                clearLostCandidate();
                transitionTo(FollowerState::INTERSECTION);
            } else if (mask == 0) {
                const uint32_t now = millis();
                if (!_lostCandidateActive) {
                    _lostCandidateActive = true;
                    _lostCandidateSinceMs = now;
                } else if ((uint32_t)(now - _lostCandidateSinceMs) >= kLostConfirmMs) {
                    clearLostCandidate();
                    transitionTo(FollowerState::LOST);
                    _lostTimer = now;
                }
            } else {
                clearLostCandidate();
                if (_turnRequested) {
                    transitionTo(FollowerState::TURNING);
                    // direction already stored via requestTurn()
                }
            }
            break;

        case FollowerState::LOST:
            if (mask != 0) {
                clearLostCandidate();
                transitionTo(FollowerState::FOLLOWING);
            } else if (millis() - _lostTimer > 500) {
                transitionTo(FollowerState::SEARCHING);
                _searchingDirection = 0; // start left
            }
            break;

        case FollowerState::SEARCHING:
            if (mask != 0) {
                clearLostCandidate();
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
    _searchingDirection = 0;
    clearLostCandidate();
}

void FollowerStateMachine::transitionTo(FollowerState newState) {
    _state = newState;
}
