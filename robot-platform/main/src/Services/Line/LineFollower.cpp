#include "LineFollower.h"
#include "LineErrorEstimator.h"
#include "MotorMixer.h"
#include <Arduino.h>
#include "../Robot/MotionConfig.h"
#include <math.h>

namespace {
constexpr float LAST_DIRECTION_THRESHOLD = 0.25f;
}

LineFollower& LineFollower::instance() {
    static LineFollower follower;
    return follower;
}

LineFollower::LineFollower()
    : _pid(1.2f, 0.02f, 0.5f, 0.02f),
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
      _scaleFactor(15.0f)
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
}

bool LineFollower::update(uint8_t mask, int speed, int &leftMotor, int &rightMotor) {
    if (_stopped) { leftMotor = rightMotor = 0; return false; }

    if (_bmpActive && millis() - _bmpStart >= _bmpDuration) {
        _bmpActive = false; _stopped = true; leftMotor = rightMotor = 0; return false;
    }

    const float error = LineErrorEstimator::estimate(mask);

    // Track the last meaningful side from the continuous five-eye estimate.
    if (error < -LAST_DIRECTION_THRESHOLD) {
        _lastLineDirection = RecoveryStrategy::DIR_LEFT;
        _recovery.setLastDirection(_lastLineDirection);
    } else if (error > LAST_DIRECTION_THRESHOLD) {
        _lastLineDirection = RecoveryStrategy::DIR_RIGHT;
        _recovery.setLastDirection(_lastLineDirection);
    }

    bool intersection = _intersectionDetector.update(mask);
    _stateMachine.update(mask, intersection, _turnRequested, _stopAtIntersectionRequested);
    FollowerState fs = _stateMachine.getState();
    bool recovering = (fs == FollowerState::LOST || fs == FollowerState::SEARCHING);

    // Keep V1 reacquire semantics for this task: any active line sensor exits
    // recovery. Center-zone-only reacquire remains a hardware-validation item.
    if (_wasRecovering && mask != 0) {
        _pid.reset();
        _recovery.reset();
    }
    _wasRecovering = recovering;

    switch (fs) {
        case FollowerState::LOST:
        case FollowerState::SEARCHING:
            _recovery.update(mask, leftMotor, rightMotor);
            return true;

        case FollowerState::INTERSECTION:
            if (_stopAtIntersectionRequested) {
                leftMotor = rightMotor = 0;
            } else {
                leftMotor = rightMotor = speed;
                _stateMachine.reset();
            }
            break;

        case FollowerState::TURNING:
            if (_turnDirection == 1) { leftMotor = -speed; rightMotor = speed; }
            else if (_turnDirection == 2) { leftMotor = speed; rightMotor = -speed; }
            else leftMotor = rightMotor = 0;
            break;

        default: {
            const int baseSpeed = constrain(speed, 0, 100);
            const float correction = _pid.update(error);
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