#include "LineFollower.h"
#include "LineErrorEstimator.h"
#include "MotorMixer.h"
#include <Arduino.h>
#include "../Robot/MotionConfig.h"
#include <math.h>

namespace {
constexpr float LAST_DIRECTION_THRESHOLD = 0.25f;
constexpr float ERROR_FILTER_ALPHA = 0.70f;
}

LineFollower& LineFollower::instance() {
    static LineFollower follower;
    return follower;
}

LineFollower::LineFollower()
    : _pid(1.0f, 0.0f, 0.0f, 0.02f),
      _speed(50),
      _stopped(false),
      _turnRequested(false),
      _turnDirection(0),
      _stopAtIntersectionRequested(false),
      _bmpActive(false),
      _bmpDuration(0),
      _lastLineDirection(RecoveryStrategy::DIR_UNKNOWN),
      _lastControlUpdate(0),
      _wasRecovering(false),
      _filteredError(0.0f),
      _filterInitialized(false),
      _lastRawError(0.0f),
      _lastFilteredError(0.0f),
      _lastCorrection(0.0f),
      _scaleFactor(12.0f)
{
    _pid.setLimits(-100, 100);
}

void LineFollower::setPIDGains(float kp, float ki, float kd) {
    _pid.setGains(kp, ki, kd);
}

void LineFollower::setPIDLimits(float min, float max) {
    _pid.setLimits(min, max);
}

void LineFollower::reset() {
    _stopped = false;
    _stateMachine.reset();
    _pid.reset();
    _bmpActive = false;
    _turnRequested = false;
    _stopAtIntersectionRequested = false;
    _lastLineDirection = RecoveryStrategy::DIR_UNKNOWN;
    _lastControlUpdate = 0;
    _wasRecovering = false;
    _filteredError = 0.0f;
    _filterInitialized = false;
    _lastRawError = 0.0f;
    _lastFilteredError = 0.0f;
    _lastCorrection = 0.0f;
    _recovery.reset();
}

void LineFollower::turnEncounterLine(int direction) {
    _turnRequested = true;
    _turnDirection = direction;
    _stateMachine.requestTurn(direction);
}

void LineFollower::stopAtIntersection() {
    _stopAtIntersectionRequested = true;
    _stateMachine.requestStopAtIntersection();
}

void LineFollower::followForBmp(int speed, int degree) {
    _bmpDuration = degree * 5;
    _bmpStart = millis();
    _bmpActive = true;
    _speed = speed;
    _stopped = false;
}

void LineFollower::stop() {
    _stopped = true;
    _stateMachine.reset();
    _pid.reset();
    _bmpActive = false;
    _filteredError = 0.0f;
    _filterInitialized = false;
    _lastRawError = 0.0f;
    _lastFilteredError = 0.0f;
    _lastCorrection = 0.0f;
}

bool LineFollower::update(uint8_t mask, int speed, int &leftMotor, int &rightMotor) {
    if (_stopped) { leftMotor = rightMotor = 0; return false; }

    if (_bmpActive && millis() - _bmpStart >= _bmpDuration) {
        _bmpActive = false; _stopped = true; leftMotor = rightMotor = 0; return false;
    }

    const float rawError = LineErrorEstimator::estimate(mask);
    _lastRawError = rawError;

    // During a short zero-mask dropout, keep the last valid steering estimate
    // instead of pulling the filter toward center. FollowerStateMachine owns
    // the 60 ms decision of whether the line is truly lost.
    if (mask != 0) {
        if (!_filterInitialized) {
            _filteredError = rawError;
            _filterInitialized = true;
        } else {
            _filteredError += ERROR_FILTER_ALPHA * (rawError - _filteredError);
        }
    }
    _lastFilteredError = _filteredError;

    // Recovery direction follows the immediate spatial observation so a mild
    // low-pass filter cannot hide which side the line was last seen on.
    if (rawError < -LAST_DIRECTION_THRESHOLD) {
        _lastLineDirection = RecoveryStrategy::DIR_LEFT;
        _recovery.setLastDirection(_lastLineDirection);
    } else if (rawError > LAST_DIRECTION_THRESHOLD) {
        _lastLineDirection = RecoveryStrategy::DIR_RIGHT;
        _recovery.setLastDirection(_lastLineDirection);
    }

    bool intersection = _intersectionDetector.update(mask);
    _stateMachine.update(mask, intersection, _turnRequested, _stopAtIntersectionRequested);
    FollowerState fs = _stateMachine.getState();
    bool recovering = (fs == FollowerState::LOST || fs == FollowerState::SEARCHING);

    // Start every real recovery from phase zero. Previously _phaseStart could
    // be stale, causing the first LOST event to jump straight into deep/sweep.
    if (recovering && !_wasRecovering) {
        _recovery.reset();
    }

    // Keep V1 reacquire semantics for this task: any active line sensor exits
    // recovery. Center-zone-only reacquire remains a hardware-validation item.
    if (_wasRecovering && mask != 0) {
        _pid.reset();
        _recovery.reset();
        _filteredError = rawError;
        _lastFilteredError = rawError;
        _filterInitialized = true;
    }
    _wasRecovering = recovering;

    switch (fs) {
        case FollowerState::LOST:
        case FollowerState::SEARCHING:
            _lastCorrection = 0.0f;
            _recovery.update(mask, leftMotor, rightMotor);
            return true;

        case FollowerState::INTERSECTION:
            _lastCorrection = 0.0f;
            if (_stopAtIntersectionRequested) {
                leftMotor = rightMotor = 0;
            } else {
                leftMotor = rightMotor = speed;
                _stateMachine.reset();
            }
            break;

        case FollowerState::TURNING:
            _lastCorrection = 0.0f;
            if (_turnDirection == 1) { leftMotor = -speed; rightMotor = speed; }
            else if (_turnDirection == 2) { leftMotor = speed; rightMotor = -speed; }
            else leftMotor = rightMotor = 0;
            break;

        default: {
            const int baseSpeed = constrain(speed, 0, 100);
            const float correction = _pid.update(_filteredError);
            _lastCorrection = correction;
            MotorOutput out = MotorMixer::mix(baseSpeed, correction, _scaleFactor);
            leftMotor = out.left;
            rightMotor = out.right;
            break;
        }
    }

    if (_stopAtIntersectionRequested && intersection) {
        _stopAtIntersectionRequested = false;
        _stopped = true;
        leftMotor = rightMotor = 0;
        return false;
    }
    if (_turnRequested && mask != 0) _turnRequested = false;
    return true;
}